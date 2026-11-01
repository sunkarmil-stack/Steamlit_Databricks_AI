# Atlas Agent Operations

A Streamlit control plane starter for governed data agents on Databricks. Create agent configurations, validate data, inspect lineage metadata, and review compliance controls from one interface.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Without Databricks credentials, the app runs with bundled sample data and metadata. To enable the SQL warehouse connection test and live table validation, provide these environment variables:

```text
DATABRICKS_HOST=https://<workspace-host>
DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/<warehouse-id>
DATABRICKS_TOKEN=<secret>
```

Use secret-backed environment variables in Databricks Apps. Do not commit credentials. The app needs permission to use the configured SQL warehouse and read the selected table. Live validation currently expects `customer_id`, `email`, and `lifetime_value` columns and reads at most 10,000 rows.

## Deploy as a Databricks App

Deploy this repository as a Streamlit Databricks App. The included `app.yaml` starts the app, and `requirements.txt` installs its Python dependencies. Add the SQL connection values through the app's environment configuration if live validation is needed.

## Current scope

- Agent creation and pause/resume controls are stored in the Streamlit session; they are not yet persisted or deployed as model-serving agents.
- Data validation can run against the bundled sample, an uploaded CSV, or a selected live table.
- Lineage and compliance inventories are representative sample metadata. Unity Catalog lineage and policy queries, durable audit storage, and model inference are integration work still to be completed.
- The compliance audit records its result in the current session only; it is not a formal compliance attestation.