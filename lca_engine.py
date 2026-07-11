import pandas as pd


def calculate_lca(foreground, background, substitution=None):

    emission_results = []
    total_emission = 0

    for _, row in foreground.iterrows():

        flow = row["Flow"]
        amount = row["Amount"]
        flow_type = row["Type"]

        if flow_type == "Input":

            match = background[background["Flow"] == flow]

            if len(match) > 0:
                ef = float(match.iloc[0]["Emission factor"])
                emission = amount * ef

                total_emission += emission

                emission_results.append(
                    {
                        "Flow": flow,
                        "Emission": emission
                    }
                )

        elif flow_type == "Emission":

            total_emission += amount

            emission_results.append(
                {
                    "Flow": flow,
                    "Emission": amount
                }
            )

    credit = 0

    if substitution is not None:

        for _, row in substitution.iterrows():

            amount = row["Amount"]
            factor = row["Credit factor"]

            credit += amount * factor

    product_data = foreground[
        foreground["Type"] == "Product"
    ]

    if len(product_data) > 0:
        product_amount = float(product_data.iloc[0]["Amount"])
    else:
        product_amount = 1

    net_emission = total_emission - credit

    carbon_footprint = net_emission / product_amount

    contribution = pd.DataFrame(emission_results)

    if len(contribution) > 0:
        contribution["Percentage"] = (
            contribution["Emission"]
            /
            contribution["Emission"].sum()
            * 100
        )

    result = {
        "Total emission": total_emission,
        "Credit": credit,
        "Net emission": net_emission,
        "Product amount": product_amount,
        "Carbon footprint": carbon_footprint
    }

    return result, contribution
