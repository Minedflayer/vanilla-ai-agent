# app.py
import streamlit as st

# Set up the page configuration
st.set_page_config(page_title="My AI Agent", page_icon="🤖")
st.title("🤖 Vanilla AI Agent")

# Initialize the chat history in Streamlit's "session state"
if "ui_messages" not in st.session_state:
    st.session_state.ui_messages = [
        {
            "role": "assistant",
            "content": "Hello! I am your AI agent. How can I help you today?",
        }
    ]

# Display the chat history
for msg in st.session_state.ui_messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# The user input box
if user_input := st.chat_input("Type your message here..."):

    # Immediately display the user's message on the screen
    with st.chat_message("user"):
        st.markdown(user_input)

    # Save it to the UI memory
    st.session_state.ui_messages.append({"role": "user", "content": user_input})

    # dummy response to test the UI
    with st.chat_message("assistant"):
        st.markdown("*(The AI is thinking... we will connect your engine here next!)*")
