import streamlit as st
from google.genai import types
import sys
from pathlib import Path

# Make sure we can import from agent directory
sys.path.append(str(Path(__file__).parent))

from main import (
    create_chat,
    send_with_retry,
    execute_tool,
    MAX_TOOL_CALLS,
    MODEL_NAME
)

st.set_page_config(
    page_title="Data Quality Agent",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 Data Quality Agent")
st.markdown(f"**Powered by:** `{MODEL_NAME}` and DuckDB")

# Initialize session state for chat memory
if "chat" not in st.session_state:
    st.session_state.chat = create_chat()
    
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if "content" in msg:
            st.markdown(msg["content"])
        
        # Display tool calls if they exist in history
        if "tool_calls" in msg:
            for tc in msg["tool_calls"]:
                with st.expander(f"🛠️ {tc['name']}"):
                    st.code(tc['result'])

# Chat input
if user_input := st.chat_input("Ask a question about your data (e.g., 'Why is revenue high today?'):"):
    
    # Render user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)
        
    # Render assistant response
    with st.chat_message("assistant"):
        status_text = st.empty()
        status_text.markdown("🔄 *Agent is thinking and investigating...*")
        
        tool_calls_ui = []
        
        def ui_log_callback(msg):
            # If it's a quota retry message, show a warning
            if "Gemini quota reached" in msg:
                status_text.warning(msg)
            # If it's a tool execution message, show it
            elif "🛠️  Tool" in msg:
                status_text.markdown(f"🔄 *{msg.strip()}*")
            elif "Maximum investigation steps" in msg:
                status_text.warning(msg)
                
        # Monkey patch execute_tool locally in app.py to intercept results for the UI
        original_execute_tool = sys.modules['main'].execute_tool
        
        def intercept_execute_tool(name, args):
            result = original_execute_tool(name, args)
            
            # Display the tool call in the UI inside an expander immediately
            with st.expander(f"🛠️ Tool: `{name}`"):
                st.write("**Arguments:**", args)
                st.code(result[:1000] + ("\n..." if len(result) > 1000 else ""))
                
            # Save to UI history
            tool_calls_ui.append({
                "name": name, 
                "result": result[:1000] + ("\n..." if len(result) > 1000 else "")
            })
            return result
            
        sys.modules['main'].execute_tool = intercept_execute_tool
        
        try:
            from main import investigate
            response = investigate(
                st.session_state.chat, 
                user_input, 
                log_callback=ui_log_callback
            )
            
            # Restore original function
            sys.modules['main'].execute_tool = original_execute_tool
                    
            # Clear status and show final text
            status_text.empty()
            
            if response.text:
                st.markdown(response.text)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response.text,
                    "tool_calls": tool_calls_ui
                })
                
                # Start a fresh context window after the investigation is complete
                st.session_state.chat = create_chat()
                
            else:
                st.error("The agent did not return a text response.")
                
        except Exception as e:
            status_text.empty()
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                st.error("❌ Gemini quota is exhausted. Please try again in a few minutes.")
            else:
                st.error(f"❌ Unexpected error: {e}")
