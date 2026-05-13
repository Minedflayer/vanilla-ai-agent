import streamlit as st
from agent import run_agent_stream
from memory import enforce_memory_limit
import uuid  # Built-in library to generate unique random IDs

# Set up the page configuration
st.set_page_config(page_title="My AI Agent", page_icon="🤖")
st.title("🤖 Vanilla AI Agent")


# Define the standard system prompt to avoid repeating it
SYSTEM_PROMPT = {
    "role": "system",
    "content": (
        "You are an advanced research assistant. "
        "If asked about current events or live data, use the 'search_web' tool. "
        "For stock prices, always search for 'current live price of [TICKER] today'. "
        "When using the calculate tool, ONLY pass simple mathematical equations. Use '*' for multiplication."
    ),
}


# ==========================================
# 1. INITIALIZE SESSION STATE
# ==========================================
if "chats" not in st.session_state:
    first_chat_id = str(uuid.uuid4())
    st.session_state.chats = {
        first_chat_id: [
            SYSTEM_PROMPT,
            {
                "role": "assistant",
                "content": "Hello! I'm now connected to your real backend. Ask me anything!",
            },
        ]
    }

    # Track which chat we are currently looking at
    st.session_state.current_chat_id = first_chat_id


# ==========================================
# SIDEBAR
# ==========================================
with st.sidebar:
    st.title("Chat History")

    # New chat button
    if st.button("➕ New Chat", use_container_width=True):
        new_chat_id = str(uuid.uuid4())
        st.session_state.chats[new_chat_id] = [
            SYSTEM_PROMPT,
            {
                "role": "assistant",
                "content": "New conversation started! Ask me anything.",
            },
        ]
        st.session_state.current_chat_id = new_chat_id
        st.rerun()

    st.divider()

    # List of previous chats
    st.subheader("Previous Chats")
    for chat_id, messages in st.session_state.chats.items():
        chat_title = "Empty"
        for msg in messages:
            if msg["role"] == "user":
                chat_title = msg["content"][:20] + "..."  # Grab first 20 chars
                break

        # Highlight the active chat visually
        is_active = chat_id == st.session_state.current_chat_id
        button_type = "primary" if is_active else "secondary"

        if st.button(
            chat_title, key=chat_id, type=button_type, use_container_width=True
        ):
            st.session_state.current_chat_id = chat_id
            st.rerun()


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

    # 1. Initialize the complex state
if "chats" not in st.session_state:
    first_chat_id = str(uuid.uuid4())
    # 'chats' is a dictionary: { chat_id: [message_list] }
    st.session_state.chats = {
        first_chat_id: [
            SYSTEM_PROMPT,
            {"role": "assistant", "content": "Hello! Ask me anything!"},
        ]
    }
    # Track which chat we are currently looking at
    st.session_state.current_chat_id = first_chat_id


# Grab the specific list of messages for whatever chat is currently active
active_messages = st.session_state.chats[st.session_state.current_chat_id]


# Display historical chat messages
for msg in active_messages:
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
