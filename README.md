# Bio-LCA Calculator v0.1

A simple Streamlit tool for process-informed life cycle assessment of bioprocesses.

## Files

- `app.py`: Streamlit user interface
- `lca_engine.py`: LCA calculation engine
- `requirements.txt`: Python dependencies
- `example_data/foreground.xlsx`: foreground LCI example
- `example_data/background.xlsx`: background emission-factor example
- `example_data/substitution.xlsx`: by-product substitution/credit example

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy on Streamlit Community Cloud

1. Upload all files and the `example_data` folder to one GitHub repository.
2. In Streamlit Community Cloud, select the repository.
3. Set the main file path to `app.py`.
4. Deploy.

## Excel column requirements

### foreground.xlsx

| Flow | Amount | Unit | Type |
|---|---:|---|---|
| Glucose | 1000 | kg | Input |
| Electricity | 500 | kWh | Input |
| Steam | 2000 | MJ | Input |
| Lactic acid | 300 | kg | Product |
| CO2 | 400 | kg | Emission |

Allowed `Type` values: `Input`, `Product`, `Emission`.

### background.xlsx

| Flow | Unit | Emission factor |
|---|---|---:|
| Glucose | kg | 0.80 |
| Electricity | kWh | 1.32 |
| Steam | MJ | 0.07 |

### substitution.xlsx

| Product | Amount | Credit factor |
|---|---:|---:|
| Protein | 50 | 2.00 |
| Heat | 100 | 0.07 |

The net carbon footprint is calculated as:

`(total emissions - substitution credits) / main product amount`
