# My AI Agent

A lightweight Streamlit chat application that connects a local UI to a Groq-powered language model and tool pipeline.

It stores conversations in a local SQLite database and supports tool-enabled responses for time, math, file reading, and live web search.

Try it out here!
https://vanilla-ai-agent-esidip9e5hbqsfkuunygze.streamlit.app/

## Features

- Streamlit chat interface with sidebar chat history
- Persistent chat storage using `chats.db`
- Tool-enabled assistant for:
  - current time lookup
  - simple calculation
  - local file reading
  - web search via Tavily
- Automatic chat title generation for new conversations
- Conversation memory trimming to keep the chat context manageable

## Getting started

### Requirements

- Python 3.10+
- `pip` package manager
- `streamlit`
- `groq`, `tavily`, `python-dotenv`

### Setup

1. Clone the repository.
2. Create a Python virtual environment.

```bash
python -m venv venv
source venv/Scripts/activate  # Windows
```

3. Install dependencies.

```bash
pip install streamlit groq tavily python-dotenv
```

4. Create a `.env` file in the project root with your API keys:

```env
GROQ_API_KEY=your_groq_api_key
TAVILY_API_KEY=your_tavily_api_key
```

5. Ensure `chats.db` is ignored by Git.

```gitignore
chats.db
```

## Run

Start the app with Streamlit:

```bash
streamlit run app.py
```

Then open the URL shown in the terminal.

## Project structure

- `app.py` - Streamlit interface, chat session management, sidebar navigation, and main chat loop
- `agent.py` - Groq client, tool definitions, streaming response handling, and chat title generation
- `database.py` - SQLite chat persistence and CRUD operations
- `memory.py` - Conversation memory pruning logic
- `safety.py` - placeholder safety configuration for tool execution

## Notes

> [!NOTE]
> `chats.db` is created at runtime and stores local chat history. It should not be committed to source control.

The app is designed for local experimentation with a simple agent architecture and tool use, not for production deployment.
