from __future__ import annotations

import os
from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import streamlit as st


st.set_page_config(
    page_title="Atlas | Agent Operations",
    page_icon="A",
    layout="wide",
    initial_sidebar_state="expanded",
)


st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap');
    :root {
        --ink: #17211d;
        --muted: #718078;
        --paper: #f5f7f3;
        --surface: #ffffff;
        --line: #e2e8e1;
        --green: #c9ef72;
        --deep-green: #315a46;
        --orange: #e88b55;
    }
    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; color: var(--ink); }
    .stApp { background: var(--paper); }
    [data-testid="stSidebar"] { background: #edf1eb; border-right: 1px solid var(--line); }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color: var(--muted); }
    .brand { display:flex; align-items:center; gap:10px; padding: 8px 0 24px; }
    .brand-mark { width:34px; height:34px; display:grid; place-items:center; background:var(--green); color:var(--ink); font-weight:700; border-radius:9px; }
    .brand-name { font-size:17px; font-weight:700; letter-spacing:0; color:var(--ink); }
    .eyebrow { font: 500 11px 'IBM Plex Mono', monospace; text-transform:uppercase; color:var(--muted); letter-spacing:0; }
    .page-title { font-size:30px; font-weight:700; line-height:1.15; margin:4px 0 6px; }
    .page-subtitle { color:var(--muted); font-size:14px; margin-bottom:22px; }
    .metric-card { background:var(--surface); border:1px solid var(--line); border-radius:8px; padding:16px 18px; min-height:104px; }
    .metric-label { color:var(--muted); font-size:12px; font-weight:600; }
    .metric-value { font-size:28px; font-weight:700; line-height:1.25; margin-top:5px; }
    .metric-note { color:var(--muted); font-size:11px; margin-top:3px; }
    .section-heading { font-size:16px; font-weight:700; margin:8px 0 12px; }
    .status-pill { display:inline-block; border-radius:20px; padding:4px 9px; font:500 11px 'IBM Plex Mono',monospace; }
    .status-good { background:#e4f2dc; color:#315a46; }
    .status-warn { background:#fff0dc; color:#8a5726; }
    .status-risk { background:#fbe5df; color:#974c3a; }
    .mono { font-family:'IBM Plex Mono',monospace; }
    div[data-testid="stForm"] { background:white; border:1px solid var(--line); border-radius:8px; padding:20px; }
    .stButton > button[kind="primary"] { background:#315a46; border-color:#315a46; color:white; }
    .stButton > button { border-radius:6px; }
    [data-testid="stDataFrame"] { border:1px solid var(--line); border-radius:8px; }
    .callout { background:#edf3e9; border-left:3px solid var(--deep-green); padding:12px 14px; border-radius:0 6px 6px 0; color:#40564a; font-size:13px; }
    </style>
    """,
    unsafe_allow_html=True,
)


def seed_state() -> None:
    if "agents" not in st.session_state:
        st.session_state.agents = [
            {
                "name": "Customer 360 steward",
                "id": "agt-0042",
                "model": "databricks-meta-llama-3-3-70b",
                "status": "Active",
                "capabilities": ["Validation", "Lineage", "Compliance"],
                "dataset": "main.crm.customer_360",
                "created": "Today, 09:14",
            },
            {
                "name": "Finance close monitor",
                "id": "agt-0038",
                "model": "databricks-dbrx-instruct",
                "status": "Active",
                "capabilities": ["Validation", "Compliance"],
                "dataset": "main.finance.monthly_close",
                "created": "Yesterday, 16:42",
            },
            {
                "name": "Supply chain lineage",
                "id": "agt-0031",
                "model": "databricks-meta-llama-3-1-8b",
                "status": "Paused",
                "capabilities": ["Lineage"],
                "dataset": "main.ops.shipments",
                "created": "Oct 28, 11:06",
            },
        ]
    if "last_validation" not in st.session_state:
        st.session_state.last_validation = None
    if "audit_complete" not in st.session_state:
        st.session_state.audit_complete = False
    if "page" not in st.session_state:
        st.session_state.page = "Overview"


seed_state()

SAMPLE_DATA = pd.DataFrame(
    {
        "customer_id": [1001, 1002, 1003, 1004, 1004, 1006],
        "email": ["ava@example.com", "li@example.com", None, "noah@example.com", "noah@example.com", "mia@example.com"],
        "country": ["US", "CA", "US", "GB", "GB", "US"],
        "lifetime_value": [240.5, 88.0, -12.0, 130.0, 130.0, 410.2],
        "updated_at": pd.to_datetime(["2026-10-29", "2026-10-29", "2026-10-30", "2026-10-30", "2026-10-30", "2026-10-31"]),
    }
)

DATASETS = [
    "main.crm.customer_360",
    "main.finance.monthly_close",
    "main.ops.shipments",
    "main.marketing.campaign_attribution",
]
LINEAGE = {
    "main.crm.customer_360": ["bronze.crm.customers", "silver.crm.customer_profile", "main.crm.customer_360"],
    "main.finance.monthly_close": ["bronze.erp.ledger", "silver.finance.journal_entries", "main.finance.monthly_close"],
    "main.ops.shipments": ["bronze.wms.shipments", "silver.ops.delivery_events", "main.ops.shipments"],
    "main.marketing.campaign_attribution": ["bronze.ad_platform.events", "silver.marketing.touchpoints", "main.marketing.campaign_attribution"],
}


def go_to(page: str) -> None:
    st.session_state.page = page


def page_header(eyebrow: str, title: str, subtitle: str) -> None:
    st.markdown(f'<div class="eyebrow">{eyebrow}</div><div class="page-title">{title}</div><div class="page-subtitle">{subtitle}</div>', unsafe_allow_html=True)


def metric(label: str, value: str, note: str) -> None:
    st.markdown(
        f'<div class="metric-card"><div class="metric-label">{label}</div><div class="metric-value">{value}</div><div class="metric-note">{note}</div></div>',
        unsafe_allow_html=True,
    )


def badge(status: str) -> str:
    tone = "good" if status in {"Active", "Passed", "Compliant", "Healthy"} else "warn" if status in {"Warning", "Review", "Paused"} else "risk"
    return f'<span class="status-pill status-{tone}">{status}</span>'


def run_validation(data: pd.DataFrame) -> list[dict[str, str]]:
    checks = [
        ("Required values", "customer_id and email must be present", int(data[["customer_id", "email"]].isna().any(axis=1).sum()), "rows"),
        ("Unique key", "customer_id must be unique", int(data["customer_id"].duplicated().sum()), "duplicates"),
        ("Non-negative value", "lifetime_value must be >= 0", int((data["lifetime_value"] < 0).sum()), "rows"),
        ("Email format", "email must contain a valid address", int((~data["email"].fillna("").str.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")).sum()), "rows"),
    ]
    return [
        {"Check": name, "Rule": rule, "Result": "Passed" if failures == 0 else "Failed", "Affected": f"{failures} {unit}"}
        for name, rule, failures, unit in checks
    ]


def open_databricks_connection(host: str, http_path: str, token: str):
    import databricks.sql

    return databricks.sql.connect(
        server_hostname=host.removeprefix("https://").rstrip("/"),
        http_path=http_path,
        access_token=token,
    )


with st.sidebar:
    st.markdown('<div class="brand"><div class="brand-mark">A</div><div class="brand-name">atlas<span style="color:#718078;font-weight:500"> / control</span></div></div>', unsafe_allow_html=True)
    st.markdown('<div class="eyebrow">Workspace</div>', unsafe_allow_html=True)
    st.markdown("**Lakehouse · Production**")
    st.caption("us-west-2 · Unity Catalog")
    st.divider()
    pages = ["Overview", "Agents", "Data quality", "Lineage", "Compliance", "Settings"]
    selected = st.radio("Control room", pages, key="page", label_visibility="collapsed")
    st.divider()
    st.markdown('<div class="eyebrow">Runtime</div>', unsafe_allow_html=True)
    st.markdown(f'{badge("Demo mode")}', unsafe_allow_html=True)
    st.caption("Configure a Databricks SQL warehouse in Settings to test connectivity and validate live tables.")

page = st.session_state.page

if page == "Overview":
    page_header("AGENT OPERATIONS / OVERVIEW", "Data agents, under control.", "Monitor the agents protecting your lakehouse data and the policies they enforce.")
    top = st.columns(4)
    with top[0]: metric("REGISTERED AGENTS", str(len(st.session_state.agents)).zfill(2), "Across 4 governed datasets")
    with top[1]: metric("ACTIVE RUNS", "03", "2 completed in the last hour")
    with top[2]: metric("QUALITY SCORE", "98.4%", "Across monitored tables")
    with top[3]: metric("POLICY COVERAGE", "92%", "11 of 12 controls passing")
    st.write("")
    left, right = st.columns([1.45, 1])
    with left:
        st.markdown('<div class="section-heading">Agent fleet</div>', unsafe_allow_html=True)
        fleet = pd.DataFrame([
            {"Agent": a["name"], "Dataset": a["dataset"], "Capabilities": ", ".join(a["capabilities"]), "Status": a["status"]}
            for a in st.session_state.agents
        ])
        st.dataframe(fleet, hide_index=True, width="stretch", column_config={"Status": st.column_config.TextColumn("Status")})
        st.markdown('<div class="section-heading" style="margin-top:22px">Recent activity</div>', unsafe_allow_html=True)
        activity = pd.DataFrame([
            {"Time": "09:42:18", "Event": "PII scan completed", "Asset": "main.crm.customer_360", "Outcome": "Passed"},
            {"Time": "09:31:04", "Event": "Uniqueness check flagged duplicates", "Asset": "main.crm.customer_360", "Outcome": "Review"},
            {"Time": "09:14:52", "Event": "Agent deployed", "Asset": "main.finance.monthly_close", "Outcome": "Passed"},
        ])
        st.dataframe(activity, hide_index=True, width="stretch")
    with right:
        st.markdown('<div class="section-heading">Governance pulse</div>', unsafe_allow_html=True)
        trend = pd.DataFrame({"Day": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"], "Quality": [96.8, 97.4, 97.1, 98.0, 97.6, 98.1, 98.4], "Coverage": [86, 87, 89, 89, 91, 91, 92]})
        chart = go.Figure()
        chart.add_trace(go.Scatter(x=trend["Day"], y=trend["Quality"], name="Quality", mode="lines+markers", line={"color": "#315a46", "width": 3}, marker={"size": 6}))
        chart.add_trace(go.Scatter(x=trend["Day"], y=trend["Coverage"], name="Policy coverage", mode="lines+markers", line={"color": "#e88b55", "width": 2, "dash": "dot"}, marker={"size": 5}))
        chart.update_layout(height=250, margin={"l": 0, "r": 4, "t": 12, "b": 0}, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", legend={"orientation": "h", "y": 1.15}, font={"family": "DM Sans", "color": "#718078"}, yaxis={"range": [80, 100], "gridcolor": "#e2e8e1", "title": None}, xaxis={"title": None, "showgrid": False})
        st.plotly_chart(chart, width="stretch", config={"displayModeBar": False})
        st.markdown('<div class="callout">1 data quality issue needs review in <span class="mono">main.crm.customer_360</span>.</div>', unsafe_allow_html=True)
    st.write("")
    st.button("+  Create an agent", type="primary", on_click=go_to, args=("Agents",))

elif page == "Agents":
    page_header("AGENT OPERATIONS / FLEET", "Agent registry", "Create governed agents and assign them the controls they are responsible for.")
    left, right = st.columns([1.05, 1.4], gap="large")
    with left:
        st.markdown('<div class="section-heading">Create agent</div>', unsafe_allow_html=True)
        with st.form("create_agent_form", clear_on_submit=True):
            name = st.text_input("Agent name", placeholder="e.g. Product analytics steward")
            dataset = st.selectbox("Primary dataset", DATASETS)
            model = st.selectbox("Serving endpoint", ["databricks-meta-llama-3-3-70b", "databricks-dbrx-instruct", "databricks-meta-llama-3-1-8b"])
            st.markdown("**Enable capabilities**")
            capabilities = [
                capability for capability, enabled in [
                    ("Validation", st.checkbox("Data validation", value=True)),
                    ("Lineage", st.checkbox("Data lineage", value=True)),
                    ("Compliance", st.checkbox("Data compliance", value=True)),
                ] if enabled
            ]
            submitted = st.form_submit_button("Create agent", type="primary", width="stretch")
        if submitted:
            if not name.strip():
                st.error("Enter a name for this agent.")
            elif not capabilities:
                st.error("Enable at least one capability.")
            else:
                agent_id = f"agt-{datetime.now().strftime('%H%M%S')}"
                st.session_state.agents.insert(0, {"name": name.strip(), "id": agent_id, "model": model, "status": "Active", "capabilities": capabilities, "dataset": dataset, "created": "Just now"})
                st.success(f"{name.strip()} created as {agent_id}.")
    with right:
        st.markdown('<div class="section-heading">Registered agents</div>', unsafe_allow_html=True)
        for agent in st.session_state.agents:
            with st.container(border=True):
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    st.markdown(f"**{agent['name']}**  ·  <span class='mono'>{agent['id']}</span>", unsafe_allow_html=True)
                    st.caption(f"{agent['dataset']}  ·  {agent['model']}")
                    st.caption(" / ".join(agent["capabilities"]))
                with col_b:
                    st.markdown(badge(agent["status"]), unsafe_allow_html=True)
                    if agent["status"] == "Active":
                        if st.button("Pause", key=f"pause_{agent['id']}"):
                            agent["status"] = "Paused"
                            st.rerun()
                    else:
                        if st.button("Resume", key=f"resume_{agent['id']}"):
                            agent["status"] = "Active"
                            st.rerun()

elif page == "Data quality":
    page_header("AGENT OPERATIONS / VALIDATION", "Data quality", "Run deterministic checks against a governed table or upload a CSV for a quick profile.")
    left, right = st.columns([1, 2], gap="large")
    with left:
        dataset_choice = st.selectbox("Catalog table", DATASETS, index=0)
        uploaded = st.file_uploader("Or validate a CSV", type=["csv"])
        live_validation = st.checkbox("Read live table from Databricks", disabled=not all(os.getenv(key) for key in ("DATABRICKS_HOST", "DATABRICKS_HTTP_PATH", "DATABRICKS_TOKEN")))
        if uploaded is not None:
            try:
                validation_data = pd.read_csv(uploaded)
            except Exception as error:
                st.error(f"Could not read CSV: {error}")
                validation_data = None
        else:
            validation_data = SAMPLE_DATA.copy()
        if validation_data is not None and not live_validation:
            st.caption(f"{len(validation_data):,} rows · {len(validation_data.columns)} columns · {dataset_choice if uploaded is None else uploaded.name}")
        run_clicked = st.button("Run validation", type="primary", disabled=validation_data is None, width="stretch")
        if run_clicked and validation_data is not None:
            if live_validation:
                connection = None
                try:
                    connection = open_databricks_connection(os.getenv("DATABRICKS_HOST", ""), os.getenv("DATABRICKS_HTTP_PATH", ""), os.getenv("DATABRICKS_TOKEN", ""))
                    validation_data = pd.read_sql_query(
                        f"SELECT customer_id, email, lifetime_value FROM {dataset_choice} LIMIT 10000",
                        connection,
                    )
                    st.caption(f"Loaded {len(validation_data):,} rows from {dataset_choice} (maximum 10,000).")
                except Exception as error:
                    st.error(f"Databricks query failed: {error}")
                    validation_data = None
                finally:
                    if connection is not None:
                        connection.close()
            if validation_data is not None:
                required_columns = {"customer_id", "email", "lifetime_value"}
                if not required_columns.issubset(validation_data.columns):
                    missing = ", ".join(sorted(required_columns - set(validation_data.columns)))
                    st.error(f"This starter rule set requires columns: {missing}")
                else:
                    st.session_state.last_validation = run_validation(validation_data)
    with right:
        st.markdown('<div class="section-heading">Validation results</div>', unsafe_allow_html=True)
        results = st.session_state.last_validation
        if results is None:
            st.info("Run validation to evaluate required values, key uniqueness, value ranges, and email format.")
        else:
            passed = sum(result["Result"] == "Passed" for result in results)
            st.markdown(f"**{passed} of {len(results)} checks passed** · last run {datetime.now().strftime('%H:%M:%S')}")
            st.dataframe(pd.DataFrame(results), hide_index=True, width="stretch")
        st.markdown('<div class="section-heading" style="margin-top:22px">Data preview</div>', unsafe_allow_html=True)
        if validation_data is not None:
            st.dataframe(validation_data.head(8), hide_index=True, width="stretch")

elif page == "Lineage":
    page_header("AGENT OPERATIONS / LINEAGE", "Trace every table.", "Explore upstream sources and downstream consumers across the Unity Catalog data flow.")
    selected_dataset = st.selectbox("Select a governed asset", DATASETS, key="lineage_dataset")
    nodes = LINEAGE[selected_dataset]
    st.markdown('<div class="section-heading">Transformation path</div>', unsafe_allow_html=True)
    cols = st.columns(len(nodes))
    for index, (column, node) in enumerate(zip(cols, nodes)):
        with column:
            st.markdown(f'<div class="eyebrow">{"SOURCE" if index == 0 else "GOVERNED TABLE" if index == len(nodes) - 1 else f"TRANSFORM {index}"}</div>', unsafe_allow_html=True)
            st.markdown(f"**`{node}`**")
            if index < len(nodes) - 1:
                st.markdown("↓")
    st.divider()
    details = pd.DataFrame([
        {"Asset": node, "Layer": "Bronze" if index == 0 else "Gold" if index == len(nodes) - 1 else "Silver", "Last updated": f"2026-11-01 {9-index:02d}:30 UTC", "Owner": "data-platform", "Classification": "Confidential" if "crm" in node or "finance" in node else "Internal"}
        for index, node in enumerate(nodes)
    ])
    st.dataframe(details, hide_index=True, width="stretch")
    st.markdown('<div class="callout">This starter view uses bundled sample lineage metadata. Unity Catalog lineage system-table queries are not yet wired in.</div>', unsafe_allow_html=True)

elif page == "Compliance":
    page_header("AGENT OPERATIONS / GOVERNANCE", "Compliance controls", "Review policy coverage, inspect sensitive data handling, and record an audit run.")
    controls = [
        {"Control": "PII columns are classified", "Scope": "Unity Catalog", "Status": "Compliant", "Evidence": "4 tables scanned"},
        {"Control": "Sensitive columns have masking policies", "Scope": "Production schemas", "Status": "Review", "Evidence": "1 column needs review"},
        {"Control": "External sharing is restricted", "Scope": "Workspace", "Status": "Compliant", "Evidence": "Policy enforced"},
        {"Control": "Agent actions are auditable", "Scope": "Agent fleet", "Status": "Compliant", "Evidence": f"{len(st.session_state.agents)} agents registered"},
        {"Control": "Retention policy is defined", "Scope": "Customer data", "Status": "Compliant", "Evidence": "365-day retention"},
    ]
    st.markdown('<div class="section-heading">Policy controls</div>', unsafe_allow_html=True)
    st.dataframe(pd.DataFrame(controls), hide_index=True, width="stretch")
    left, right = st.columns([1, 1], gap="large")
    with left:
        st.markdown('<div class="section-heading">Sensitive data inventory</div>', unsafe_allow_html=True)
        inventory = pd.DataFrame([
            {"Table": "main.crm.customer_360", "Column": "email", "Classification": "PII", "Policy": "email_mask"},
            {"Table": "main.crm.customer_360", "Column": "customer_id", "Classification": "Direct identifier", "Policy": "restricted_access"},
            {"Table": "main.finance.monthly_close", "Column": "account_number", "Classification": "Financial", "Policy": "account_mask"},
        ])
        st.dataframe(inventory, hide_index=True, width="stretch")
    with right:
        st.markdown('<div class="section-heading">Audit run</div>', unsafe_allow_html=True)
        st.write("Evaluate the configured controls and record a timestamped review in this session.")
        if st.button("Run compliance audit", type="primary"):
            st.session_state.audit_complete = True
        if st.session_state.audit_complete:
            st.success(f"Audit recorded at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}. 4 controls compliant; 1 flagged for review.")
        else:
            st.caption("No audit run recorded in this session.")

elif page == "Settings":
    page_header("AGENT OPERATIONS / SETTINGS", "Workspace connection", "Configure optional Databricks SQL access for warehouse connectivity and live-table validation.")
    host = os.getenv("DATABRICKS_HOST", "")
    http_path = os.getenv("DATABRICKS_HTTP_PATH", "")
    token = os.getenv("DATABRICKS_TOKEN", "")
    configured = bool(host and http_path and token)
    st.markdown('<div class="callout">For Databricks Apps, set these values as app environment variables or secrets. Credentials are never stored in the browser session.</div>', unsafe_allow_html=True)
    st.write("")
    left, right = st.columns([1, 1], gap="large")
    with left:
        st.markdown('<div class="section-heading">Connection details</div>', unsafe_allow_html=True)
        st.text_input("Workspace host", value=host, placeholder="https://your-workspace.cloud.databricks.com", disabled=True)
        st.text_input("SQL warehouse HTTP path", value=http_path, placeholder="/sql/1.0/warehouses/...", disabled=True)
        st.text_input("Personal access token", value="Configured" if token else "", type="password", placeholder="Set DATABRICKS_TOKEN", disabled=True)
        st.caption("Edit app environment variables in the Databricks Apps configuration.")
    with right:
        st.markdown('<div class="section-heading">Connection status</div>', unsafe_allow_html=True)
        st.markdown(badge("Configured" if configured else "Demo mode"), unsafe_allow_html=True)
        if configured:
            if st.button("Test SQL warehouse connection", type="primary"):
                connection = None
                try:
                    connection = open_databricks_connection(host, http_path, token)
                    cursor = connection.cursor()
                    cursor.execute("SELECT 1")
                    cursor.fetchone()
                    cursor.close()
                    st.success("Connected to the Databricks SQL warehouse.")
                except Exception as error:
                    st.error(f"Connection failed: {error}")
                finally:
                    if connection is not None:
                        connection.close()
        else:
            st.info("No Databricks SQL credentials detected. Live validation is disabled; the app is using sample data.")
        st.markdown("**Required environment variables**")
        st.code("DATABRICKS_HOST\nDATABRICKS_HTTP_PATH\nDATABRICKS_TOKEN", language="text")
