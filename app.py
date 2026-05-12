# app.py
import streamlit as st
from agent import client, MODEL_ID, tools_list, available_functions
from memory import enforce_memory_limit
import json

# Set up the page configuration
st.set_page_config(page_title="My AI Agent", page_icon="🤖")
st.title("🤖 Vanilla AI Agent")

# Initialize the chat history in Streamlit's "session state"
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system",
            "content": "Hello! I am your AI agent. How can I help you today?",
        },
        {
            "role": "assistant",
            "content": "Hello! I'm now connected to your real backend. Ask me anything!",
        },
    ]

# Display the chat history
for msg in st.session_state.messages:
    # Skip the hidden system prompt
    if msg["role"] == "system":
        continue

    # Normal User Messages
    if msg["role"] == "user":
        with st.chat_message("user"):
            st.markdown(msg["content"])

    # Assistant Messages
    elif msg["role"] == "assistant":
        # If the AI actually spoke text, print it
        if msg.get("content"):
            with st.chat_message("assistant"):
                st.markdown(msg["content"])

    # Tool Results
    elif msg["role"] == "tool":
        # Recreate the dropdown status box for historical tool uses
        with st.chat_message("assistant"):
            with st.status(f"🛠️ Used Tool: {msg['name']}", state="complete"):
                st.write(msg["content"])

# User Input
if user_input := st.chat_input("Ask me about blue whales or the stock market..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

# The Brain Connection
with st.chat_message("assistant"):
    response_placeholder = st.empty()
    full_response = ""

    # Run agent loop
    while True:
        st.session_state.messages = enforce_memory_limit(
            st.session_state.messages, max_messages=20
        )

        response = client.chat.completions.create(
            model=MODEL_ID,
            messages=st.session_state.messages,
            tools=tools_list,
            tool_choice="auto",
            stream=True,
        )

        tool_call_buffer = {}

        for chunk in response:
            delta = chunk.choices[0].delta
            if delta.content:
                full_response += delta.content
                response_placeholder.markdown(full_response + "▌")

            if delta.tool_calls:
                for tc_chunk in delta.tool_calls:
                    idx = tc_chunk.index
                    if idx not in tool_call_buffer:
                        tool_call_buffer[idx] = {
                            "id": tc_chunk.id,
                            "type": "function",
                            "function": {
                                "name": tc_chunk.function.name,
                                "arguments": "",
                            },
                        }
                    if tc_chunk.function.arguments:
                        tool_call_buffer[idx]["function"][
                            "arguments"
                        ] += tc_chunk.function.arguments
        response_placeholder.markdown(full_response)

        if tool_call_buffer:
            tool_calls_list = list(tool_call_buffer.values())
            # Add the tool request to history
            st.session_state.messages.append(
                {"role": "assistant", "tool_calls": tool_calls_list}
            )

            for tc in tool_calls_list:
                f_name = tc["function"]["name"]
                f_args = json.loads(tc["function"]["arguments"])

                with st.status(f"🛠️ Tool: {f_name}...", expanded=False):
                    # Dynamic execution
                    func = available_functions[f_name]

                    obs = func(**f_args) if f_args else func()
                    st.write(f"Result: {str(obs)[:100]}...")

                # Add the result to history
                st.session_state.messages.append(
                    {
                        "tool_call_id": tc["id"],
                        "role": "tool",
                        "name": f_name,
                        "content": str(obs),
                    }
                )
        else:
            # No more tools needed, finalize text
            st.session_state.messages.append(
                {"role": "assistant", "content": full_response}
            )
            break
