import sqlite3
import json

DB_FILE = "chats.db"


def init_db():
    """Creates the database and the chats table if they don't exist."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # We create a table with an ID, a Title, and a JSON string of the messages
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chats (
            id TEXT PRIMARY KEY,
            title TEXT,
            messages TEXT
        )
    """)
    conn.commit()
    conn.close()


def save_chat(chat_id, title, messages):
    """Inserts or updates a chat in the database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Convert the Python list of dictionaries into a JSON string
    messages_json = json.dumps(messages)

    # UPSERT: Insert the new row, but if the ID already exists, update it instead
    cursor.execute(
        """
        INSERT INTO chats (id, title, messages)
        VALUES (?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            title = excluded.title,
            messages = excluded.messages
    """,
        (chat_id, title, messages_json),
    )

    conn.commit()
    conn.close()


def load_all_chats():
    """Retrieves all chats from the database and returns them as a dictionary."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("SELECT id, title, messages FROM chats")
    rows = cursor.fetchall()
    conn.close()

    # Reconstruct the dictionary format that app.py expects: { id: [messages] }
    chats_dict = {}
    for row in rows:
        chat_id = row[0]
        # We will use the title later, but for now we just need the messages
        messages = json.loads(row[2])
        chats_dict[chat_id] = messages

    return chats_dict


# Helper function that fetches title
def get_chat_title(chat_id):
    """Fetches just the title for a specific chat ID."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT title FROM chats WHERE id = ?", (chat_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else "New chat"


def delete_chat(chat_id):
    """Permanently removes a chat and its messages from the database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM chats WHERE id = ?", (chat_id,))
    conn.commit()
    conn.close()
