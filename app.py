import streamlit as st
from agent import run_agent_stream, generate_chat_title
from memory import enforce_memory_limit
import uuid  # Built-in library to generate unique random IDs
from database import init_db, save_chat, load_all_chats, get_chat_title, delete_chat


# ==========================================
# 1. UI CUSTOMIZATION (CSS INJECTION)
# ==========================================
def apply_custom_styles():
    st.markdown(
        """
        <style>
            /* Style the Sidebar Header  */
            [data-testid="stSidebar"] h1 { 
                font-size: 1.15rem !important;     
                font-weight: 600 !important;
                color: #1f1f1f !important;
                margin-bottom: -15px !important;    /* Pull the divider UP */
                padding-bottom: 0 !important;
            }

            /* Style the Sidebar Divider (st.divider) */
            [data-testid="stSidebar"] hr {
                margin-top: 0px !important;         /* Remove space above the line */
                margin-bottom: 1rem !important;     /* Keep some space below the line */
                border-top: 1px solid #e5e5e5 !important;
            }
            
            /* Ensure the 'Previous Chats' subheader matches the font */
            [data-testid="stSidebar"] h3 {
                font-size: 0.9rem !important;
                font-weight: 600 !important;
                color: #444746 !important;
            }

            /* Reset all Sidebar Buttons to look like List Items */
            [data-testid="stSidebar"] .stButton > button {
                width: 100%;
                border: none;
                background-color: transparent;
                text-align: left;
                justify-content: flex-start; /* Align text to left */
                padding: 0.6rem 1rem;
                border-radius: 8px;
                transition: all 0.2s ease;
                color: #444;
                font-weight: 400;
            }

            /* Hover State: Subtle background change */
            [data-testid="stSidebar"] .stButton > button:hover {
                background-color: #ececec !important;
                color: #000 !important;
            }

            /* Active State */
            /* We target buttons with kind="primary" inside the sidebar */
            [data-testid="stSidebar"] .stButton > button[kind="primary"] {
                background-color: #e8f0fe !important; /* Subtle blue tint */
                color: #1a73e8 !important;          /* Active blue text */
                border-left: 4px solid #1a73e8 !important; /* Vertical active bar */
                border-radius: 0 8px 8px 0 !important;   /* Flat edge on left */
                font-weight: 600;
            }

            /* Hide the redundant focus borders */
            [data-testid="stSidebar"] .stButton > button:focus {
                box-shadow: none !important;
                outline: none !important;
            }

            /* Main Sidebar Container */
            [data-testid="stSidebar"] {
                background-color: #f9f9f9; /* Subtle off-white/gray */
                border-right: 1px solid #e5e5e5;
            }

            /* Remove default padding from the sidebar content */
            [data-testid="stSidebar"] > div:first-child {
                padding-left: 0.5rem;
                padding-right: 0.5rem;
                border-radius: 2rem;
            }

            /* Target the Main App Container (where the chat lives) */
            [data-testid="stAppViewContainer"] {
                background-color: #ffffff;
            }

            /* Create the "Centered Column" look for the chat */
            [data-testid="stMainViewContainer"] > div:first-child > div:first-child {
                max-width: 850px;
                margin: 0 auto;
            }

            /* The Button Container - Refined Alignment */
            [data-testid="stSidebar"] .st-key-new_chat_btn button {
                border: none !important;
                background-color: transparent !important;
                display: flex !important;
                align-items: center !important;
                justify-content: flex-start !important;
                padding: 0.5rem 1.2rem !important; /* Slightly more side padding */
                height: 48px !important;           /* Slightly taller for 'airiness' */
                width: 100% !important;
                color: #444746 !important;
                transition: all 0.2s ease;
            }

            /* New chat icon */
            [data-testid="stSidebar"] .st-key-new_chat_btn button::before {
                content: "";
                display: inline-block;
                width: 24px !important;            /* Increased from 20px */
                height: 24px !important;           /* Increased from 20px */
                margin-right: 14px !important;     /* Better spacing for a 24px icon */
                background-color: #444746;         /* Match text color exactly */
                
                /* Icon Logic */
                -webkit-mask-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="black" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.375 2.625a1 1 0 0 1 3 3l-9.013 9.014a2 2 0 0 1-.853.505l-2.873.84a.5.5 0 0 1-.62-.62l.84-2.873a2 2 0 0 1 .506-.852z"/></svg>');
                mask-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="black" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.375 2.625a1 1 0 0 1 3 3l-9.013 9.014a2 2 0 0 1-.853.505l-2.873.84a.5.5 0 0 1-.62-.62l.84-2.873a2 2 0 0 1 .506-.852z"/></svg>');
                
                /* New chat icon sizing: use 100% to fill the 24px container perfectly */
                -webkit-mask-size: 100%;
                mask-size: 100%;
                -webkit-mask-repeat: no-repeat;
                mask-repeat: no-repeat;
                -webkit-mask-position: center;
                mask-position: center;
            }

            /* Hover State - Consistent with the list */
            [data-testid="stSidebar"] .st-key-new_chat_btn button:hover {
                background-color: #eef2f8 !important; /* Soft Gemini-blue hover */
                color: #1f1f1f !important;
            }
        }
        </style>
    """,
        unsafe_allow_html=True,
    )


apply_custom_styles()

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
    if st.button("New Chat", key="new_chat_btn", use_container_width=True):
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
        chat_title = get_chat_title(chat_id)
        is_active = chat_id == st.session_state.current_chat_id
        button_type = "primary" if is_active else "secondary"

        if st.button(
            chat_title, key=chat_id, type=button_type, use_container_width=True
        ):
            st.session_state.current_chat_id = chat_id
            st.rerun()

    st.divider()

    # This button only acts on the chat you are currently looking at
    if st.button("🗑️ Delete Current Chat", use_container_width=True, type="secondary"):
        chat_id_to_del = st.session_state.current_chat_id

        # Delete from Database and remove from session_state
        delete_chat(chat_id_to_del)
        if chat_id_to_del in st.session_state.chats:
            del st.session_state.chats[chat_id_to_del]

        if not st.session_state.chats:
            # If no chats left, the app will recreate a blank one on refresh
            st.rerun()
        else:
            # Switch to the first available chat
            st.session_state.current_chat_id = list(st.session_state.chats.keys())[0]
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

    # If the user only has 1 message in this chat (plus the system prompt/greeting),
    # generate a title. Otherwise, grab the existing title from the database.
    # ---------------------------------------------------------
    user_message_count = sum(1 for msg in active_messages if msg["role"] == "user")

    if user_message_count == 1:
        chat_title = generate_chat_title(user_input)
    else:
        # If it is not the first message, keep the existing title from db_chats
        # Look what is currently in the DB
        db_chats = load_all_chats()

    # Update the database with the user's new message
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

                # Update the database with the AI's final response
                save_chat(
                    st.session_state.current_chat_id, chat_title, event["messages"]
                )
