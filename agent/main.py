import os
import random
import re
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types

from tools import (
    get_dbt_lineage,
    get_dq_history,
    get_model_sql,
    get_schema,
    list_tables,
    query_duckdb,
)


# ============================================================
# Configuration
# ============================================================

load_dotenv()

# Using Vertex AI with Application Default Credentials (ADC)
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")

MODEL_NAME = os.getenv("MODEL_NAME", "gemini-3.5-flash-lite")

# IMPORTANT for free-tier quota
MAX_TOOL_CALLS = int(os.getenv("MAX_TOOL_CALLS", "6"))

# Prevent very large tool responses from going back to Gemini.
MAX_RESULT_CHARS = int(os.getenv("MAX_RESULT_CHARS", "3500"))

# Maximum number of application-level retries for 429.
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "2"))

# Add a small delay between API calls.
MIN_API_DELAY = float(os.getenv("MIN_API_DELAY", "1.5"))


# ============================================================
# Gemini client
# ============================================================

# --- Option 1: Vertex AI (Current Active Method) ---
client = genai.Client(vertexai=True, project=PROJECT_ID)

# --- Option 2: Google AI Studio (API Key) ---
# To switch back, comment out Option 1 and uncomment the code below:
# API_KEY = os.getenv("GEMINI_API_KEY")
# if not API_KEY:
#     raise RuntimeError("GEMINI_API_KEY not found in .env")
# client = genai.Client(api_key=API_KEY)


# ============================================================
# Agent instructions
# ============================================================

SYSTEM_INSTRUCTION = """
You are a senior Data Quality Engineer and an autonomous
Data Quality Root Cause Analysis Agent.

Your mission is to investigate data quality incidents and
identify the most likely root cause using real data.

You are NOT a generic chatbot.

Your job is:

1. Verify the reported anomaly.
2. Compare it with historical behavior.
3. Inspect the affected table schema.
4. Trace dbt lineage.
5. Inspect relevant upstream models.
6. Inspect transformation SQL when useful.
7. Investigate likely causes.
8. Quantify the impact when possible.
9. Recommend a practical fix.

Available tools:

- list_tables()
  List available DuckDB tables.

- query_duckdb(query)
  Run read-only SQL against DuckDB.

- get_schema(table_name)
  Inspect table structure.

- get_dbt_lineage(model_name)
  Inspect upstream/downstream dbt dependencies.

- get_model_sql(model_name)
  Inspect dbt transformation SQL.

- get_dq_history(table_name, metric_column, date_column, days)
  Inspect historical metric behavior.

Investigation rules:

- Start by verifying the anomaly.
- Prefer actual database evidence over assumptions.
- Use historical data when possible.
- Follow lineage upstream.
- Inspect SQL if a transformation or join could explain the issue.
- Look for:
  * duplicates
  * NULL explosions
  * broken joins
  * many-to-many joins
  * unexpected filters
  * missing records
  * volume anomalies
  * incorrect aggregations
  * schema changes
  * unexpected values
- Do not invent evidence.
- Do not stop at the first symptom.
- Do not make unnecessary tool calls.
- Prioritize the highest-value investigation steps.
- You have a limited investigation budget, so be efficient.

When enough evidence is available, return:

## Incident

What is wrong?

## Investigation

What did you check?

## Root cause

What most likely caused the issue?

## Evidence

What concrete observations support the conclusion?

## Impact

What data is affected?

## Recommended fix

What should be changed?

## Confidence

Give a confidence score from 0% to 100%.

If evidence is insufficient, say so explicitly.
"""


# ============================================================
# Tools
# ============================================================

TOOLS = [
    list_tables,
    query_duckdb,
    get_schema,
    get_dbt_lineage,
    get_model_sql,
    get_dq_history,
]


TOOL_MAP = {
    "list_tables": list_tables,
    "query_duckdb": query_duckdb,
    "get_schema": get_schema,
    "get_dbt_lineage": get_dbt_lineage,
    "get_model_sql": get_model_sql,
    "get_dq_history": get_dq_history,
}


# ============================================================
# Helper functions
# ============================================================

def extract_retry_seconds(error_message: str):
    """
    Extract retry delay from Gemini error message.

    Example:
        'Please retry in 42.868071556s.'
    """

    match = re.search(
        r"retry in ([0-9.]+)s",
        error_message,
        re.IGNORECASE,
    )

    if not match:
        return None

    try:
        return float(match.group(1))
    except ValueError:
        return None


def send_with_retry(chat, message, log_callback=None):
    """
    Send a message to Gemini with controlled 429 handling.

    The Gemini SDK already handles transient retries, but this
    catches quota errors that still reach the application.
    
    log_callback: Optional function that takes a string message to log.
    """

    for attempt in range(MAX_RETRIES + 1):

        try:
            # Small spacing between requests.
            if attempt == 0:
                time.sleep(MIN_API_DELAY)

            return chat.send_message(message)

        except Exception as exc:

            error_message = str(exc)

            is_429 = (
                "429" in error_message
                or "RESOURCE_EXHAUSTED" in error_message
                or "quota" in error_message.lower()
            )

            if not is_429:
                raise

            if attempt >= MAX_RETRIES:
                raise

            retry_seconds = extract_retry_seconds(
                error_message
            )

            if retry_seconds is None:
                # Exponential backoff if Google does not
                # provide an explicit retry delay.
                retry_seconds = min(
                    5 * (2 ** attempt),
                    60,
                )

            # Add a little jitter.
            retry_seconds += random.uniform(0.5, 1.5)

            msg = (
                f"⏳ Gemini quota reached. "
                f"Retrying in {retry_seconds:.1f}s..."
            )
            
            if log_callback:
                log_callback(msg)
            else:
                print(f"\n{msg}")

            time.sleep(retry_seconds)


def execute_tool(function_name: str, args: dict):
    """
    Execute the requested local tool.
    """

    function = TOOL_MAP.get(function_name)

    if function is None:
        return f"ERROR: Unknown tool '{function_name}'."

    try:
        result = function(**args)

        if result is None:
            return "Tool returned no result."

        result = str(result)

        if len(result) > MAX_RESULT_CHARS:
            result = (
                result[:MAX_RESULT_CHARS]
                + "\n\n...[OUTPUT TRUNCATED]"
            )

        return result

    except Exception as exc:
        return (
            f"ERROR executing {function_name}: "
            f"{exc}"
        )


# ============================================================
# Chat initialization
# ============================================================

def create_chat():
    """
    Create the Gemini chat session.
    """

    return client.chats.create(
        model=MODEL_NAME,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,

            tools=TOOLS,

            temperature=0,

            # Keep final responses reasonably small.
            max_output_tokens=1500,
        ),
    )


# ============================================================
# Agent
# ============================================================

def investigate(chat, user_input: str, log_callback=None):
    """
    Run one complete investigation.
    """

    tool_call_count = 0

    response = send_with_retry(
        chat,
        user_input,
        log_callback=log_callback
    )

    while response.function_calls:

        for function_call in response.function_calls:

            # Global investigation budget.
            if tool_call_count >= MAX_TOOL_CALLS:

                msg = (
                    "\n⚠️ Maximum investigation steps "
                    "reached. Asking the agent to summarize."
                )
                
                if log_callback:
                    log_callback(msg)
                else:
                    print(msg)

                response = send_with_retry(
                    chat,
                    (
                        "You have reached the maximum number "
                        "of investigation tool calls. "
                        "Stop investigating and provide the "
                        "best root-cause analysis you can "
                        "based only on the evidence collected."
                    ),
                    log_callback=log_callback
                )

                return response

            tool_call_count += 1

            name = function_call.name
            args = function_call.args or {}

            msg = (
                f"\n🛠️  Tool {tool_call_count}/"
                f"{MAX_TOOL_CALLS}: "
                f"{name}({args})"
            )
            if log_callback is None:
                print(msg)

            result = execute_tool(
                name,
                args,
            )
            
            if log_callback is None:
                print(
                    f"   ↳ {result[:1000]}"
                    + (
                        "\n   ↳ ..."
                        if len(result) > 1000
                        else ""
                    )
                )

            response = send_with_retry(
                chat,
                types.Part.from_function_response(
                    name=name,
                    response={
                        "result": result
                    },
                ),
                log_callback=log_callback
            )

    return response


# ============================================================
# CLI
# ============================================================

def run_agent():

    print("=" * 70)
    print("🤖 DATA QUALITY ROOT CAUSE AGENT")
    print("=" * 70)

    print("\nModel:")
    print(f"  {MODEL_NAME}")

    print("\nAvailable tools:")
    print("  ✓ DuckDB SQL")
    print("  ✓ Table schema")
    print("  ✓ dbt lineage")
    print("  ✓ dbt SQL")
    print("  ✓ DQ history")

    print(
        f"\nMaximum tool calls per investigation: "
        f"{MAX_TOOL_CALLS}"
    )

    print("\nExample:")
    print(
        "  Why is revenue in mart_sales unusually "
        "high today?"
    )

    print("\nType 'exit' to quit.\n")

    while True:

        try:

            user_input = input("You: ").strip()

            if not user_input:
                continue

            if user_input.lower() in {
                "exit",
                "quit",
            }:
                print("\nGoodbye 👋")
                break

            print(
                "\n🤖 Agent is investigating..."
            )

            chat = create_chat()

            try:

                response = investigate(
                    chat,
                    user_input,
                )

            except Exception as exc:

                error_message = str(exc)

                if (
                    "429" in error_message
                    or "RESOURCE_EXHAUSTED"
                    in error_message
                ):
                    print(
                        "\n❌ Gemini quota is still "
                        "exhausted after retries."
                    )

                    print(
                        "The code is working, but the "
                        "Gemini project quota is currently "
                        "unavailable."
                    )

                    print(
                        "\nTry again after the quota "
                        "window resets or use a paid "
                        "API project."
                    )

                else:
                    print(
                        f"\n❌ Agent error: {exc}"
                    )

                continue

            print("\n" + "=" * 70)
            print("🤖 ROOT CAUSE ANALYSIS")
            print("=" * 70)

            if response.text:
                print(response.text)
            else:
                print(
                    "The agent did not return a text response."
                )

            print("=" * 70 + "\n")

        except KeyboardInterrupt:

            print(
                "\n\nInterrupted. Goodbye 👋"
            )
            break

        except Exception as exc:

            print(
                f"\n❌ Unexpected error: {exc}\n"
            )


if __name__ == "__main__":
    run_agent()