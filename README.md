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
Inside your Ubuntu terminal, make sure Python and Git are installed:
```bash
sudo apt update && sudo apt upgrade -y
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

Your database is now fully built and resides locally in `data/duckdb/hackathon.duckdb`. It is ready to be queried by Tableau or the Qualitia AI Agent!
