
from __future__ import annotations

import io
import math

import numpy as np
import pandas as pd


def _to_numeric(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    result = df.copy()
    for col in columns:
        if col in result.columns:
            result[col] = pd.to_numeric(result[col], errors="coerce")
    return result


def calculate_lca(
    inventory: pd.DataFrame,
    background: pd.DataFrame,
    credits: pd.DataFrame,
    transport_mass_t: float,
    return_trip: bool,
) -> dict:
    errors: list[str] = []

    inv = _to_numeric(inventory, ["Amount"]).dropna(
        subset=["Unit process", "Flow", "Amount", "Type"]
    )
    bg = _to_numeric(background, ["Emission factor"]).dropna(
        subset=["Flow", "Unit", "Emission factor"]
    )
    cr = _to_numeric(credits, ["Amount", "Credit factor"]).dropna(
        subset=["By-product", "Amount", "Credit factor"]
    )

    product_rows = inv[inv["Type"] == "Product"]
    product_amount = (
        float(product_rows["Amount"].sum()) if not product_rows.empty else 0.0
    )
    if product_amount <= 0:
        errors.append("A product row with amount greater than zero is required.")

    records: list[dict] = []
    total_emissions = 0.0

    for _, row in inv.iterrows():
        process = str(row["Unit process"]).strip()
        flow = str(row["Flow"]).strip()
        amount = float(row["Amount"])
        unit = str(row["Unit"]).strip()
        flow_type = str(row["Type"]).strip()

        if amount < 0:
            errors.append(f"{process} / {flow}: amount cannot be negative.")
            continue

        if flow_type == "Product":
            continue

        if flow_type == "Input":
            match = bg[
                (bg["Flow"].astype(str).str.strip() == flow)
                & (bg["Unit"].astype(str).str.strip() == unit)
            ]
            if match.empty:
                errors.append(
                    f"Missing background factor for {flow} ({unit})."
                )
                continue
            factor = float(match.iloc[0]["Emission factor"])
            activity = amount
            gwp = activity * factor

        elif flow_type == "Transport":
            match = bg[
                (bg["Flow"].astype(str).str.strip() == flow)
                & (bg["Unit"].astype(str).str.strip() == "t·km")
            ]
            if match.empty:
                errors.append(
                    f"Missing transport factor for {flow} (t·km)."
                )
                continue
            factor = float(match.iloc[0]["Emission factor"])
            activity = amount * max(transport_mass_t, 0.0)
            if return_trip:
                activity *= 2
            unit = "t·km"
            gwp = activity * factor

        elif flow_type == "Direct emission":
            factor = 1.0
            activity = amount
            gwp = activity

        else:
            errors.append(f"{process} / {flow}: invalid Type.")
            continue

        total_emissions += gwp
        records.append(
            {
                "Unit process": process,
                "Flow": flow,
                "Activity": activity,
                "Unit": unit,
                "Emission factor": factor,
                "GWP": gwp,
            }
        )

    total_credits = (
        float((cr["Amount"] * cr["Credit factor"]).sum())
        if not cr.empty
        else 0.0
    )
    net_emissions = total_emissions - total_credits
    carbon_footprint = (
        net_emissions / product_amount if product_amount > 0 else math.nan
    )

    detail = pd.DataFrame(records)
    if detail.empty:
        by_process = pd.DataFrame(columns=["Unit process", "GWP"])
    else:
        by_process = (
            detail.groupby("Unit process", as_index=False)["GWP"].sum()
            .sort_values("GWP", ascending=False)
        )

    return {
        "total_emissions": total_emissions,
        "total_credits": total_credits,
        "net_emissions": net_emissions,
        "product_amount": product_amount,
        "carbon_footprint": carbon_footprint,
        "detail": detail,
        "by_process": by_process,
        "errors": errors,
    }


def run_sensitivity(
    inventory: pd.DataFrame,
    background: pd.DataFrame,
    credits: pd.DataFrame,
    flow_name: str,
    lower_pct: float,
    upper_pct: float,
    steps: int,
    transport_mass_t: float,
    return_trip: bool,
) -> pd.DataFrame:
    match = background[background["Flow"].astype(str) == str(flow_name)]
    if match.empty:
        return pd.DataFrame()

    base_factor = float(match.iloc[0]["Emission factor"])
    changes = np.linspace(lower_pct, upper_pct, steps)
    rows = []

    for change in changes:
        modified = background.copy()
        mask = modified["Flow"].astype(str) == str(flow_name)
        modified.loc[mask, "Emission factor"] = base_factor * (1 + change / 100)

        result = calculate_lca(
            inventory=inventory,
            background=modified,
            credits=credits,
            transport_mass_t=transport_mass_t,
            return_trip=return_trip,
        )
        if not result["errors"]:
            rows.append(
                {
                    "Change (%)": float(change),
                    "Emission factor": base_factor * (1 + change / 100),
                    "Carbon footprint": result["carbon_footprint"],
                }
            )

    return pd.DataFrame(rows)


def build_excel_report(
    project_name: str,
    product_name: str,
    functional_unit: str,
    system_boundary: str,
    allocation_method: str,
    inventory: pd.DataFrame,
    background: pd.DataFrame,
    credits: pd.DataFrame,
    result: dict,
) -> bytes:
    output = io.BytesIO()

    summary = pd.DataFrame(
        {
            "Item": [
                "Project",
                "Product",
                "Functional unit",
                "System boundary",
                "Allocation method",
                "Total emissions (kg CO2e)",
                "Total credits (kg CO2e)",
                "Net emissions (kg CO2e)",
                "Product amount",
                "Carbon footprint",
            ],
            "Value": [
                project_name,
                product_name,
                functional_unit,
                system_boundary,
                allocation_method,
                result["total_emissions"],
                result["total_credits"],
                result["net_emissions"],
                result["product_amount"],
                result["carbon_footprint"],
            ],
        }
    )

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        summary.to_excel(writer, sheet_name="Summary", index=False)
        inventory.to_excel(writer, sheet_name="Foreground inventory", index=False)
        background.to_excel(writer, sheet_name="Background database", index=False)
        credits.to_excel(writer, sheet_name="Substitution credits", index=False)
        result["detail"].to_excel(writer, sheet_name="Contribution detail", index=False)

    return output.getvalue()
