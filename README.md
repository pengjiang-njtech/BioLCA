# ThermoLCA v1.0

A Streamlit application for process-informed life cycle assessment.

## Features

- Unit-process foreground inventory
- Dedicated transportation calculation in t·km
- Editable built-in background database
- Substitution / avoided-burden credits
- GWP contribution analysis
- One-at-a-time sensitivity analysis
- Excel report export
- No Excel upload required

## Deploy on Streamlit Community Cloud

Upload these files to the root of one GitHub repository:

```text
app.py
engine.py
defaults.py
requirements.txt
README.md
```

Then set:

```text
Main file path: app.py
```

## Important

The default emission factors are demonstration values. Replace them with verified data before formal scientific use.
