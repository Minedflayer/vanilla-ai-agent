import streamlit as st
from agent import run_agent_stream
from memory import enforce_memory_limit

# Set up the page configuration
st.set_page_config(page_title="My AI Agent", page_icon="🤖")
st.title("🤖 Vanilla AI Agent")

# Initialize the chat history
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system",
            "content": (
                "You are an advanced research assistant. "
                "If asked about current events or live data, use the 'search_web' tool. "
                "For stock prices, always search for 'current live price of [TICKER] today'. "
                "When using the calculate tool, ONLY pass simple mathematical equations. Use '*' for multiplication."
            ),
        },
        {
            "role": "assistant",
            "content": "Hello! I'm now connected to your real backend. Ask me anything!",
        },
    ]

# Display historical chat messages
for msg in st.session_state.messages:
    if msg["role"] == "system":
        continue

    if msg["role"] in ["user", "assistant"] and msg.get("content"):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    elif msg["role"] == "tool":
        with st.chat_message("assistant"):
            with st.status(f"🛠️ Used Tool: {msg['name']}", state="complete"):
                st.write(msg["content"])

# User Input
if user_input := st.chat_input("Ask me about blue whales or the stock market..."):

    # 1. Save user input and enforce limits
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.session_state.messages = enforce_memory_limit(
        st.session_state.messages, max_messages=20
    )

    # 2. Draw user message
    with st.chat_message("user"):
        st.markdown(user_input)

    # 3. Stream the Agent's response
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""

        # Loop through the events yielded by the Brain
        for event in run_agent_stream(st.session_state.messages):

            if event["event"] == "text_chunk":
                full_response += event["content"]
                response_placeholder.markdown(full_response + "▌")

            elif event["event"] == "tool_start":
                st.toast(f"🛠️ Agent is running `{event['name']}`...")

            elif event["event"] == "tool_result":
                # Optional: You can print a quick debug line to the UI if you want
                pass

            elif event["event"] == "done":
                # Finalize text and update our session state memory
                response_placeholder.markdown(full_response)
                st.session_state.messages = event["messages"]
