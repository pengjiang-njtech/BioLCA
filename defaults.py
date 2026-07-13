
from __future__ import annotations

import pandas as pd


PROCESS_ORDER = [
    "Feedstock",
    "Transportation",
    "Pretreatment",
    "Fermentation",
    "Separation",
    "Utilities",
    "Product",
]

PROCESS_ICONS = {
    "Feedstock": "🌱",
    "Transportation": "🚚",
    "Pretreatment": "🧪",
    "Fermentation": "🫙",
    "Separation": "⚗️",
    "Utilities": "⚡",
    "Product": "📦",
}

DEFAULT_INVENTORY = pd.DataFrame(
    [
        ["Feedstock", "Corn stover", 1000.0, "kg", "Input", ""],
        ["Transportation", "8 t diesel truck", 50.0, "km", "Transport", ""],
        ["Pretreatment", "Dilute sulfuric acid", 15.0, "kg", "Input", ""],
        ["Pretreatment", "Steam", 500.0, "MJ", "Input", ""],
        ["Fermentation", "Electricity", 120.0, "kWh", "Input", ""],
        ["Fermentation", "Steam", 200.0, "MJ", "Input", ""],
        ["Fermentation", "CO2 biogenic", 0.0, "kg CO2e", "Direct emission", ""],
        ["Separation", "Steam", 1500.0, "MJ", "Input", ""],
        ["Separation", "Cooling water", 10.0, "m3", "Input", ""],
        ["Utilities", "Electricity", 200.0, "kWh", "Input", ""],
        ["Utilities", "Natural gas", 50.0, "MJ", "Input", ""],
        ["Product", "Ethanol", 186.0, "kg", "Product", ""],
    ],
    columns=["Unit process", "Flow", "Amount", "Unit", "Type", "Notes"],
)

DEFAULT_BACKGROUND = pd.DataFrame(
    [
        ["Material", "Corn stover", "kg", 0.0324, 0.0, 0.0, "Example"],
        ["Material", "Dilute sulfuric acid", "kg", 0.35, 0.0, 0.0, "Example"],
        ["Energy", "Electricity", "kWh", 0.3000, 0.0, 3.000, "CLCD example"],
        ["Energy", "Steam", "MJ", 0.0700, 0.0, 0.0, "Example"],
        ["Utility", "Cooling water", "m3", 0.0840, 0.0, 0.0, "Example"],
        ["Fuel", "Natural gas", "MJ", 0.0727, 54.267, 1.189, "CLCD example"],
        ["Fuel", "Raw coal", "MJ", 0.1017, 20.908, 1.180, "CLCD example"],
        ["Fuel", "Hard coal", "MJ", 0.1287, 26.800, 1.350, "CLCD example"],
        ["Fuel", "Diesel", "MJ", 0.1055, 42.652, 1.300, "CLCD example"],
        ["Fuel", "Gasoline", "MJ", 0.0905, 43.070, 1.174, "CLCD example"],
        ["Transport", "8 t diesel truck", "t·km", 0.1655, 0.0, 1.909, "CLCD example"],
        ["Transport", "8 t gasoline truck", "t·km", 0.1374, 0.0, 2.065, "CLCD example"],
        ["Transport", "2 t diesel truck", "t·km", 0.2468, 0.0, 3.745, "CLCD example"],
    ],
    columns=[
        "Category",
        "Flow",
        "Unit",
        "Emission factor",
        "LHV",
        "Fossil energy intensity",
        "Source",
    ],
)

DEFAULT_CREDITS = pd.DataFrame(
    [
        ["Excess electricity", 20.0, "kWh", "Grid electricity", 0.3000],
        ["Biogas", 220.0, "MJ", "Natural gas", 0.0727],
        ["Animal feed", 5.0, "kg", "Conventional feed", 0.6200],
    ],
    columns=[
        "By-product",
        "Amount",
        "Unit",
        "Reference product",
        "Credit factor",
    ],
)
