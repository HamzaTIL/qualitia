# 🤖 Qualitia: AI Data Quality Agent

An AI-powered Data Quality Agent built for our internal AI Hackathon.

The goal of this project is to help business users determine whether an unexpected KPI variation is caused by a real business event or by a data quality issue. 

Instead of simply reporting failed dbt tests, the agent investigates the entire data pipeline, analyzes metadata, and explains the root cause in natural language.

---

## 🚀 Project Goals

The AI Agent should be able to:
- Detect data quality issues and analyze dbt test results.
- Understand dbt lineage and query the data warehouse (DuckDB).
- Explain anomalies using LLMs (e.g., Claude/OpenAI).
- Assist business users directly from their dashboards (e.g., Tableau).

**Example:**
> "Sales dropped by 35% today. Is this a real business issue or a data quality problem?"
> *The agent investigates the pipeline before answering.*

---

## 🏗️ Data Architecture & Modeling

Our data foundation relies on the [Olist Brazilian E-Commerce Dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce), processed via **DuckDB** and transformed using **dbt (Data Build Tool)**.

We follow a modern "Medallion / Kimball" hybrid architecture, culminating in **One Big Tables (OBTs)**:

```text
       Raw Parquet Files (Olist E-Commerce Data)
                           │
                           ▼
                        DuckDB 
                           │
             ┌─────────────┴─────────────┐
             ▼                           ▼
        Staging Layer (stg_)      Basic cleanup, typing, and renaming.
             │
             ▼
    Intermediate Layer            (dim_ / fct_) Star schema building blocks.
             │                    Separates entities (Customers, Sellers) 
             │                    from events (Orders, Items).
             ▼
        Marts Layer               Highly denormalized "One Big Tables" (OBTs).
  (mart_obt_customers)            Pre-joined, wide tables ready for AI and BI.
  (mart_obt_sellers)
  (mart_obt_orders)
                           │
         ┌─────────────────┴─────────────────┐
         ▼                                   ▼
  Tableau/BI Dashboards              Qualitia AI Agent
```

### 🧠 Why This Architecture?

1. **Supercharging the AI Agent (Qualitia):** LLMs are prone to hallucination when forced to write complex `JOIN`s across 7+ tables. By providing highly denormalized OBTs (`mart_obt_orders`, `mart_obt_sellers`), Qualitia can easily answer complex natural language questions (e.g., *"Show me delayed orders in Sao Paulo with 1-star reviews"*) with simple `SELECT` statements.
2. **Business Intelligence (BI) Friendly:** Dashboards load instantly, and business users can drag-and-drop metrics without needing to understand SQL or database relationships.
3. **Concrete Business Use Cases:**
   - **Customer 360:** Using `mart_obt_customers`, segment high-value customers against those with poor review experiences.
   - **Supply Chain Optimization:** Use `mart_logistics_network` to find delivery routes that consistently miss estimated arrival dates.
   - **Catalog Management:** Use `mart_product_performance` to prune inventory that generates negative reviews.

---

## 🤖 Qualitia Data Quality Agent Architecture

The AI agent is located in the `agent/` folder and operates as an autonomous Data Quality Root Cause Analysis engine powered by Google Gemini (e.g., `gemini-3.5-flash-lite`).

### Core Components
- **Agent Orchestrator (`main.py`):** Utilizes the `google-genai` SDK to handle the LLM tool-calling loop autonomously. It enforces strict bounds (e.g., maximum of 6 tool calls per investigation) and includes robust retry mechanisms to gracefully handle rate limits (HTTP 429 errors).
- **Interactive Web UI (`app.py`):** A newly developed Streamlit web application providing a conversational UI. It intercepts and visualizes the agent's background tool executions (e.g., SQL queries, lineage tracing) via expandable UI blocks and automatically manages the context window between investigations.
- **Custom Tool Suite (`tools.py`):** The agent is equipped with native integration directly into the data stack:
  - `query_duckdb`: Executes read-only exploratory SQL against the `hackathon.duckdb` database.
  - `list_tables` & `get_schema`: Inspects the data warehouse's structure.
  - `get_dbt_lineage`: Traces up/downstream dbt dependencies by parsing the compiled `manifest.json`.
  - `get_model_sql`: Views the transformation logic (compiled/raw SQL) behind dbt models.
  - `get_dq_history`: Analyzes metrics over historical time windows to pinpoint when anomalies began.

---

## 🛠️ Getting Started (From Scratch)

This guide is written for **non-technical users** setting up the project on a Windows machine from scratch.

### Step 1: Install WSL (Windows Subsystem for Linux)
Modern data tools run best on Linux. Windows users can run Linux natively using WSL.
1. Open your Windows **Start Menu**, search for **PowerShell**, right-click it, and select **"Run as Administrator"**.
2. Type the following command and press Enter:
   ```powershell
   wsl --install
   ```
3. Restart your computer if prompted.
4. After restarting, open the **Start Menu** and search for **Ubuntu** to open your new Linux terminal. It will ask you to create a username and password. 
   > ⚠️ **IMPORTANT:** Remember this password! It will not show characters on the screen as you type it. You will need to enter this password anytime you run an administrator command (commands starting with `sudo`).

### Step 2: Install Prerequisites in Ubuntu
Inside your Ubuntu terminal, copy and run these two commands **one by one**:
```bash
sudo apt update && sudo apt upgrade -y
```

```bash
sudo apt install python3 python3-pip python3-venv git -y
```

### Step 3: Clone the Repository
It is best practice to keep your projects in your home directory. We will navigate there and download the code. 

Because this repository is private, you cannot just use your GitHub password. You need to create a **Fine-grained Personal Access Token (PAT)**. This acts as a secure, temporary password that only has access to this specific project.

**How to generate your token:**
1. Click this exact link to go to your GitHub Token settings: [https://github.com/settings/personal-access-tokens/new](https://github.com/settings/personal-access-tokens/new)
2. **Token name:** Give it a name you will remember (e.g., `qualitia-hackathon-laptop`).
3. **Expiration:** Set it to **90 days** (or longer, depending on how long you will be working on the project).
4. **Repository access:** Select **"Only select repositories"**, then search for and select the `qualitia` repository.
5. **Permissions:** Click on **"Repository permissions"**, find **"Contents"**, and change it from "No access" to **"Read and write"**. (You need write access to save your work and push code back to GitHub).
6. Scroll to the bottom and click the green **Generate token** button.
7. **Important:** Copy the generated token immediately! It will start with `github_pat_`. You will never be able to see it again once you leave the page.

Now, open your Ubuntu terminal and navigate to your home directory:

```bash
# Go to your home directory
cd ~
```

You have two options to clone the repository using your token:

**Option A: Enter the token when prompted (Recommended)**
```bash
git clone https://github.com/HamzaTIL/qualitia.git
```
*Git will ask for your `Username` (type your GitHub username) and your `Password` (paste your `github_pat_...` token here. Remember, characters won't show on the screen as you paste!).*

**Option B: Include the token directly in the command**
```bash
# Replace 'YOUR_TOKEN' with the github_pat_... you just copied
git clone https://YOUR_TOKEN@github.com/HamzaTIL/qualitia.git
```

Once downloaded, enter the project folder:
```bash
cd qualitia
```

### Step 4: Set Up a Python Virtual Environment
A virtual environment keeps the project's dependencies isolated from the rest of your computer.

```bash
# Create the virtual environment named 'qualitia-venv'
python3 -m venv qualitia-venv

# Activate it
source qualitia-venv/bin/activate

# Install the required packages (dbt, DuckDB, Pandas, etc.)
pip install -r requirements.txt
```

**🔥 Pro Tip: Automate the Activation**
To avoid having to type `source qualitia-venv/bin/activate` every time you open a new terminal, you can tell your terminal to do it automatically:

```bash
echo "source ~/qualitia/qualitia-venv/bin/activate" >> ~/.bashrc
```
*(Now, every time you open Ubuntu, your terminal prompt will automatically start with `(qualitia-venv)`).*

### Step 5: Open the Project in VS Code
To view and edit the code, we recommend using Visual Studio Code. Assuming you have VS Code installed on your Windows machine, it will seamlessly connect to your new Linux environment.

Make sure you are still inside the `qualitia` folder in your terminal, then type:
```bash
code .
```
*(The dot `.` means "open the current folder"). This will launch VS Code. If a pop-up appears asking to install the "WSL" extension, click **Install**.*

### Step 6: Run the Data Pipeline (dbt)
Now, we instruct dbt to read the raw Parquet files (which are already included in the repository), build the DuckDB database, and create all our models (Staging -> Intermediate -> Marts).
```bash
cd dbt
dbt run
```
*If everything is successful, you will see green `[OK]` messages for all 24 models!*

Your database is now fully built and resides locally in `data/duckdb/hackathon.duckdb`. It is ready to be queried by Tableau, the Qualitia AI Agent, or via the built-in DuckDB UI!

### Step 7: Explore Your Data with the DuckDB Web UI (Optional)
DuckDB features a beautiful, built-in, local web-based User Interface (UI) where you can easily run SQL queries against your database directly in your browser.

> ⚠️ **Prerequisite:** The `duckdb` command-line tool (CLI) must be installed on your system. The Python package installed via `requirements.txt` only provides the Python client library bindings, not the terminal CLI utility itself.
>
> To quickly install the CLI and configure it on your Ubuntu/WSL system, run these commands:
> ```bash
> # 1. Download and install the latest DuckDB CLI
> curl https://install.duckdb.org | sh
>
> # 2. Add it to your terminal PATH so the 'duckdb' command is recognized
> echo 'export PATH="$HOME/.duckdb/cli/latest:$PATH"' >> ~/.bashrc
> source ~/.bashrc
> ```

There are two easy ways to launch the UI and load your database:

#### Option A: Load Your Database Directly on Launch (Recommended)
You can launch the DuckDB CLI with both the `-ui` flag and your database file path. DuckDB will automatically load the database into your session:

1. Make sure you are in the project folder in your terminal:
   ```bash
   cd ~/qualitia
   ```
2. Start the DuckDB UI with the database:
   ```bash
   duckdb data/duckdb/hackathon.duckdb -ui
   ```
   *(DuckDB will automatically download and install the built-in UI extension if it's your first time running this command).*

#### Option B: Load the Database from Inside the UI
If you have already launched the UI using just `duckdb -ui` (without a database file), you can still attach your database file by running an `ATTACH` SQL command inside the UI:

1. Start the empty UI:
   ```bash
   duckdb -ui
   ```
2. In the query editor of the web UI, run the following SQL command to connect your database:
   ```sql
   ATTACH 'data/duckdb/hackathon.duckdb' AS hackathon;
   ```
   *(You can then expand the schema tree on the left sidebar to see all of your dbt marts and tables!).*

#### 🌐 Accessing the UI in Your Browser
When you run either of the commands above:
- DuckDB will launch a local server and try to open your default browser.
- If it does not open automatically (especially when running inside WSL), simply open your favorite browser (Chrome, Edge, Firefox) on your computer and navigate to:
  ```text
  http://localhost:4213
  ```
- To stop the server and close the UI when you are done, go back to your terminal and press `Ctrl + C`.

#### 🔍 Query Examples (Interactive SQL Notebook)
The DuckDB Web UI operates as an **interactive SQL Notebook** (similar to Jupyter Notebooks or Hex). You can write multiple queries in separate "cells," execute them independently by clicking **Run** (or pressing `Shift + Enter`), and inspect automatic data diagnostics (like Null % and value histograms) on the right sidebar. Your notebooks are saved locally and automatically restored next time you open the UI!

Once you have loaded your database, you can run these query examples inside your notebook cells:

##### Example 1: Querying your Mart Tables
Since our database file is named `hackathon.duckdb`, DuckDB mounts it with the database name `hackathon`. Combined with our dbt custom schema configuration, all of your mart tables are accessible directly at `hackathon.marts.<table_name>` (or simply `marts.<table_name>`).

Here is a query to analyze seller performance metrics directly:
```sql
SELECT
    seller_id,
    state AS seller_state,
    total_orders,
    ROUND(total_revenue_usd, 2) AS total_revenue_usd,
    ROUND(delay_rate_pct, 1) AS delay_rate_pct,
    ROUND(avg_review_score, 2) AS avg_review_score,
    total_negative_reviews,
    CASE 
        WHEN avg_review_score >= 4.5 AND delay_rate_pct <= 5 THEN 'Super Seller (Excellent Score & Delivery)'
        WHEN avg_review_score <= 3.0 OR delay_rate_pct >= 25 THEN 'High Risk / Rogue (Bad Score or Extreme Delays)'
        ELSE 'Standard Seller'
    END AS seller_classification
FROM hackathon.marts.mart_obt_sellers
WHERE total_orders >= 50
ORDER BY total_revenue_usd DESC, avg_review_score ASC
LIMIT 15;
```

##### Example 2: Querying a Raw Parquet File Directly
DuckDB also allows you to query raw files (such as `.parquet`, `.csv`, `.json`) directly on disk simply by specifying their path inside the `FROM` clause:
```sql
SELECT 
    customer_state,
    COUNT(*) AS total_customers
FROM 'data/olist/olist_customers.parquet'
GROUP BY 1
ORDER BY 2 DESC
LIMIT 5;
```

---

### 📥 Step 8: Exporting Mart Tables to CSV (Optional)
If you need to load the fully built dbt marts into another tool (like Excel, Python, or another BI tool), we provide an automated script to export all mart tables directly to CSV:

1. Make sure you are in the project folder and your virtual environment is active:
   ```bash
   cd ~/qualitia
   ```
2. Run the export script:
   ```bash
   python3 export_marts_to_csv.py
   ```
This will automatically connect to your local DuckDB database, scan the `marts` schema, and save all 8 tables as CSV files under the `data/csv/` directory (created automatically).

*(Note: These exported CSV files are ignored by Git to prevent repository bloat).*



