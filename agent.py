import os
import json
import datetime
from groq import Groq
from tavily import TavilyClient
from dotenv import load_dotenv
from memory import enforce_memory_limit

load_dotenv()
# ==========================================
# 1. SETUP THE CLIENTS
# ==========================================
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
MODEL_ID = "llama-3.1-8b-instant"


# ==========================================
# 2. DEFINE YOUR TOOLS
# ==========================================
def get_current_time() -> str:
    """Returns the current date and time."""
    return str(datetime.datetime.now())


def calculate(expression: str) -> str:
    """Evaluates a mathematical expression."""
    try:
        clean_expr = expression.replace("x", "*").replace("X", "*").replace(",", "")
        return str(eval(clean_expr))
    except Exception as e:
        return f"Error: {e}"


def read_file(filepath: str) -> str:
    """Reads a local text file."""
    try:
        with open(filepath, "r") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {e}"


# --- TAVILY SEARCH TOOL ---
def search_web(query: str) -> str:
    """Searches the internet using Tavily and returns clean, AI-optimized summaries."""
    try:
        # Tavily does all the heavy lifting of scraping and summarizing
        response = tavily_client.search(query=query, search_depth="basic")

        # Format the clean data into a string for the Llama model
        formatted_results = ""
        for result in response.get("results", []):
            formatted_results += f"Title: {result['title']}\nURL: {result['url']}\nContent: {result['content']}\n\n"

        return formatted_results if formatted_results else "No results found."
    except Exception as e:
        return f"Error searching the web: {e}"


# Map the string names to the actual Python functions
available_functions = {
    "get_current_time": get_current_time,
    "calculate": calculate,
    "read_file": read_file,
    "search_web": search_web,
}

# The JSON schemas for the AI
tools_list = [
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Returns the current date and time.",
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Evaluates a math expression.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "The math expression (e.g., '5 + 5')",
                    }
                },
                "required": ["expression"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Reads a local text file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "The file path to read",
                    }
                },
                "required": ["filepath"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Searches the live internet for up-to-date information, news, and facts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query."}
                },
                "required": ["query"],
            },
        },
    },
]


# ==========================================
# 3. THE LIVE CHAT LOOP
# ==========================================

# MOVE MEMORY OUTSIDE: We put the messages array outside the loop
# so it doesn't get erased every time you ask a new question!
messages = [
    {
        "role": "system",
        "content": (
            "You are an advanced research assistant. "
            "If asked about current events or live data, use the 'search_web' tool. "
            "For stock prices, always search for 'current live price of [TICKER] today'. "
            "When using the calculate tool, ONLY pass simple mathematical equations. Use '*' for multiplication."
        ),
    }
]


def start_chat():
    print("🤖 Agent initialized! (Type 'exit' or 'quit' to close)")

    global messages

    # --- Outer Loop for the user interaction ---
    while True:

        messages = enforce_memory_limit(messages, max_messages=6)

        # Get user's input from terminal
        user_input = input("\n[You]: ")

        if user_input.lower() in ["exit", "quit"]:
            print("Bye bye")
            break

        # Add your new question to the agent's memory
        messages.append({"role": "user", "content": user_input})

        # --- THE INNER LOOP (Agent Thinking & Tools) ---
        while True:
            response = client.chat.completions.create(
                model=MODEL_ID,
                messages=messages,
                tools=tools_list,
                tool_choice="auto",
                stream=True,
            )

            final_text = ""
            tool_call_buffer = {}

            # Print the agent's prefix
            print("🤖 [Agent]: ", end="")

            for chunk in response:
                delta = chunk.choices[0].delta

                if delta.content:
                    print(delta.content, end="", flush=True)
                    final_text += delta.content

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

            # --- THE STREAM IS FINISHED ---
            # 👇 LOOK HERE: See how 'if' is perfectly lined up vertically with 'for'?
            if tool_call_buffer:
                tool_calls_list = list(tool_call_buffer.values())
                messages.append({"role": "assistant", "tool_calls": tool_calls_list})

                for tc in tool_calls_list:
                    function_name = tc["function"]["name"]
                    function_args = json.loads(tc["function"]["arguments"])

                    print(
                        f"\n   [Thought]: Calling '{function_name}' with {function_args}"
                    )
                    function_to_call = available_functions[function_name]

                    if function_name == "get_current_time":
                        obs = function_to_call()
                    else:
                        obs = function_to_call(**function_args)

                    print(f"   [Tool Output]: {str(obs)[:200]}...")

                    messages.append(
                        {
                            "tool_call_id": tc["id"],
                            "role": "tool",
                            "name": function_name,
                            "content": str(obs),
                        }
                    )
            else:
                # If no tools were called, save the text and break the inner loop!
                messages.append({"role": "assistant", "content": final_text})
                print()
                break


if __name__ == "__main__":
    start_chat()
