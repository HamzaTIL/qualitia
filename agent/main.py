import os
from google import genai
from google.genai import types
from tools import query_duckdb, get_dbt_lineage
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure the Gemini API key
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("❌ Error: GEMINI_API_KEY not found.")
    print("Please create a .env file in the root directory and add: GEMINI_API_KEY=your_api_key_here")
    exit(1)

# Initialize the new SDK client
client = genai.Client(api_key=api_key)

# Investigation instructions
system_instruction="""You are a senior Data Quality Engineer and an autonomous Agent. 
Your goal is to investigate data anomalies in a DuckDB + dbt pipeline.

You have access to tools:
1. `query_duckdb`: Use this to run SQL and inspect the actual data in DuckDB.
2. `get_dbt_lineage`: Use this to trace where a data model comes from.

Investigation Workflow:
- If a user reports a data anomaly (e.g., "Revenue is too high"), first use `query_duckdb` to verify the anomaly in the relevant mart table.
- Use `get_dbt_lineage` to find the upstream tables feeding that mart.
- Query those upstream tables (staging, intermediate, sources) using `query_duckdb` to isolate where the data starts going wrong.
- Formulate a clear explanation for the user on what is causing the issue."""

def run_agent():
    print("🤖 Data Quality Agent initialized.")
    print("I have access to your DuckDB database and your dbt lineage.")
    print("Type 'exit' to quit.\n")
    
    # Initialize chat session with the new SDK, providing the Python functions directly as tools
    chat = client.chats.create(
        model='gemini-3.1-flash-lite',
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            tools=[query_duckdb, get_dbt_lineage],
            temperature=0
        )
    )
    
    while True:
        try:
            user_input = input("You: ")
            if user_input.lower() in ['exit', 'quit']:
                break
                
            print("\n🤖 Agent is investigating...")
            response = chat.send_message(user_input)
            
            # Loop to handle potentially multiple turns of tool calls
            while response.function_calls:
                for function_call in response.function_calls:
                    name = function_call.name
                    args = function_call.args
                    
                    print(f"   [Tool Call] 🛠️  {name}({args})")
                    
                    # Execute the tool
                    try:
                        if name == "query_duckdb":
                            tool_result = query_duckdb(**args)
                        elif name == "get_dbt_lineage":
                            tool_result = get_dbt_lineage(**args)
                        else:
                            tool_result = f"Error: Unknown tool {name}"
                    except Exception as e:
                        tool_result = f"Tool execution failed: {str(e)}"
                    
                    # Send the result back to the model
                    response = chat.send_message(
                        types.Part.from_function_response(
                            name=name,
                            response={"result": tool_result}
                        )
                    )
            
            if response.text:
                print(f"🤖 Agent: {response.text}\n")
            
        except Exception as e:
            print(f"❌ Error during execution: {e}")

if __name__ == "__main__":
    run_agent()