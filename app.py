import streamlit as st
from agent import run_agent_stream
from memory import enforce_memory_limit
import uuid  # Built-in library to generate unique random IDs
from database import init_db, save_chat, load_all_chats

# Set up the page configuration
st.set_page_config(page_title="My AI Agent", page_icon="🤖")

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
# 1. INITIALIZE DATABASE & SESSION STATE
# ==========================================

init_db()

if "chats" not in st.session_state:
    db_chats = load_all_chats()

    if db_chats:
        # If we found chats, load them into session state!
        st.session_state.chats = db_chats
        # Set active chat to the last one in the db
        st.session_state.current_chat_id = list(db_chats.keys())[-1]
    else:
        first_chat_id = str(uuid.uuid4())
        initial_messages = [
            SYSTEM_PROMPT,
            {
                "role": "assistant",
                "content": "Hello! I'm now connected to your real backend. Ask me anything!",
            },
        ]
        st.session_state.chats = {first_chat_id: initial_messages}
        st.session_state.current_chat_id = first_chat_id

        # Save new chat to db
        save_chat(first_chat_id, "New Chat", initial_messages)


# ==========================================
# SIDEBAR
# ==========================================
with st.sidebar:
    st.title("💬 Chat History")
    if st.button("➕ New Chat", use_container_width=True):
        new_chat_id = str(uuid.uuid4())
        initial_messages = [
            SYSTEM_PROMPT,
            {
                "role": "assistant",
                "content": "New conversation started! Ask me anything.",
            },
        ]
        st.session_state.chats[new_chat_id] = initial_messages
        st.session_state.current_chat_id = new_chat_id

        # Save in DB
        save_chat(new_chat_id, "New Chat", initial_messages)

        st.rerun()

    st.divider()

    st.subheader("Previous Chats")
    for chat_id, messages in st.session_state.chats.items():
        # Real autogenreatd titles will be used in the near future
        chat_title = "Empty Chat"
        for msg in messages:
            if msg["role"] == "user":
                chat_title = msg["content"][:20] + "..."
                break
        is_active = chat_id == st.session_state.current_chat_id
        button_type = "primary" if is_active else "secondary"

        if st.button(
            chat_title, key=chat_id, type=button_type, use_container_width=True
        ):
            st.session_state.current_chat_id = chat_id
            st.rerun()


# ==========================================
# 3. MAIN CHAT INTERFACE
# ==========================================
st.title("🤖 Vanilla AI Agent")

active_messages = st.session_state.chats[st.session_state.current_chat_id]

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

if user_input := st.chat_input("Ask me about blue whales or the stock market..."):

    active_messages.append({"role": "user", "content": user_input})
    active_messages = enforce_memory_limit(active_messages, max_messages=20)
    st.session_state.chats[st.session_state.current_chat_id] = active_messages

    # SAVE TO DB: Update the database with the user's new message
    save_chat(st.session_state.current_chat_id, "Chat", active_messages)

    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""

        for event in run_agent_stream(active_messages):

            if event["event"] == "text_chunk":
                full_response += event["content"]
                response_placeholder.markdown(full_response + "▌")

            elif event["event"] == "tool_start":
                st.toast(f"🛠️ Agent is running `{event['name']}`...")

            elif event["event"] == "tool_result":
                pass

            elif event["event"] == "done":
                response_placeholder.markdown(full_response)
                st.session_state.chats[st.session_state.current_chat_id] = event[
                    "messages"
                ]

                # SAVE TO DB: Update the database with the AI's final response
                save_chat(st.session_state.current_chat_id, "Chat", event["messages"])
