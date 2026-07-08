# 🤖 AI Data Quality Agent

An AI-powered Data Quality Agent built for our internal AI Hackathon.

The goal of this project is to help business users determine whether an unexpected KPI variation is caused by a real business event or by a data quality issue.

Instead of simply reporting failed dbt tests, the agent investigates the entire data pipeline, analyzes metadata, and explains the root cause in natural language.

---

# 🚀 Project Goals

The AI Agent should be able to:

- Detect data quality issues
- Analyze dbt test results
- Understand dbt lineage
- Query the data warehouse
- Explain anomalies using Claude
- Notify teams through Slack
- Assist business users directly from Tableau

Example:

> "Sales dropped by 35% today. Is this a real business issue or a data quality problem?"

The agent investigates before answering.

---

# 🏗️ Architecture

```text
                           Weekly Pipeline

                     CSV / Parquet files
                             │
                             ▼
                         DuckDB (Raw)
                             │
                      dbt transformations
                             │
              ┌──────────────┴──────────────┐
              ▼                             ▼
        Silver Models                 Gold Models
                                             │
                                             ▼
                                    Tableau Dashboard
                                             │
              "Revenue dropped by 35%, investigate."
                                             │
                                             ▼
                                  AI Data Quality Agent
                                             │
         ┌───────────────────┬───────────────┼────────────────┐
         │                   │               │                │
         ▼                   ▼               ▼                ▼
   Query DuckDB      Read dbt Tests    Read Lineage     Claude API
                      run_results.json  manifest.json
         │                   │               │
         └───────────────────┴───────────────┘
                             │
                             ▼
                     Root Cause Analysis
                             │
               ┌─────────────┴─────────────┐
               ▼                           ▼
         Slack Notification         User Response
```

---

# 🔎 How it works

## 1. Data ingestion

Every week, new datasets are received (CSV or Parquet).

These files are loaded into DuckDB.

---

## 2. Data transformation

dbt Core builds the analytical models.

```
Raw
   │
   ▼
Staging
   │
   ▼
Dimensions
   │
   ▼
Fact Tables
```

dbt also executes data quality tests.

---

## 3. Business monitoring

Business users consult Tableau dashboards.

If they notice an anomaly, they can ask the AI Agent:

> "Is this KPI reliable?"

---

## 4. Investigation

The AI Agent behaves like a Data Engineer.

Instead of guessing, it collects evidence.

It can:

- Execute SQL queries on DuckDB
- Read dbt test results
- Analyze dbt lineage
- Understand model dependencies

---

## 5. Reasoning

Claude receives all collected information.

Example:

- Revenue decreased by 38%
- dbt test `not_null(customer_id)` failed
- `fct_sales` depends on `stg_sales`

Claude concludes:

> This is probably a data quality issue caused by the sales ingestion pipeline rather than a genuine decrease in business activity.

---

## 6. Alerting

The agent can automatically send Slack notifications.

Example:

```
🚨 Data Quality Alert

Dataset:
Sales

Issue:
customer_id contains NULL values

Impacted dashboard:
Sales Overview

Recommendation:
Investigate the ingestion pipeline before communicating KPIs.
```

---

# 🛠️ Tech Stack

- Python
- DuckDB
- dbt Core
- Claude (Anthropic)
- Slack Webhooks
- Tableau

---

# Why DuckDB?

We intentionally chose DuckDB for this hackathon because the objective is to demonstrate an AI-powered Data Quality Agent, not cloud infrastructure.

DuckDB allows us to:

- Develop locally with zero infrastructure
- Eliminate cloud configuration overhead
- Focus on AI capabilities
- Keep the project fully reproducible
- Remain compatible with dbt Core

Since our transformations are built with dbt, the project can later be migrated to Databricks, Snowflake or BigQuery with minimal changes.

---

# Project Structure

```text
qualitia/
│
├── README.md
├── requirements.txt
├── .gitignore
├── .env.example
│
├── data/
│   ├── raw/
│   │   ├── ventes_historiques.csv
│   │   └── ventes_du_jour.csv
│   │
│   ├── duckdb/
│   │   └── hackathon.duckdb      # ignored by git
│   │
│   └── generate_data.py
│
├── dbt_qualitia/                     # dbt project
│   ├── dbt_project.yml
│   ├── profiles.yml
│   │
│   ├── models/
│   │   ├── sources/
│   │   ├── staging/
│   │   ├── intermediate/
│   │   ├── marts/
│   │   └── schema.yml
│   │
│   ├── macros/
│   ├── tests/
│   ├── snapshots/
│   ├── analyses/
│   └── seeds/
│
├── agent/
│   ├── main.py
│   │
│   ├── tools/
│   │   ├── sql_tool.py
│   │   ├── dbt_tool.py
│   │   ├── lineage_tool.py
│   │   └── slack_tool.py
│   │
│   ├── prompts/
│   │   └── system_prompt.md
│   │
│   └── utils/
│
├── docs/
│
└── scripts/
```

---

# Getting Started

Clone the repository.

```bash
git clone <repository-url>
cd hackathon-data-quality-agent
```

Create a virtual environment.

```bash
python -m venv .venv
```

Activate it.

Linux/macOS

```bash
source .venv/bin/activate
```

Windows

```powershell
.venv\Scripts\activate
```

Install dependencies.

```bash
pip install -r requirements.txt
```

Run dbt.

```bash
cd dbt_qualitia

dbt debug
dbt seed
dbt run
dbt test
```

Run the AI Agent.

```bash
python agent/main.py
```

---

# Roadmap

- [ ] Build Bronze / Silver / Gold models
- [ ] Create realistic retail datasets
- [ ] Implement SQL Tool
- [ ] Implement dbt Artifact Tool
- [ ] Implement Lineage Tool
- [ ] Integrate Claude
- [ ] Implement Slack notifications
- [ ] Integrate Tableau
- [ ] End-to-end AI investigation workflow

---

# Future Improvements

- LangGraph multi-agent architecture
- Automatic root cause analysis
- Semantic Layer integration
- Self-healing recommendations
- Databricks support
- Snowflake support

---

# Team

Built during the AI Hackathon 🚀