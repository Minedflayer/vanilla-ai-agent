import os
import json
import datetime
from groq import Groq
from tavily import TavilyClient
from dotenv import load_dotenv

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


def search_web(query: str) -> str:
    """Searches the internet using Tavily and returns clean, AI-optimized summaries."""
    try:
        response = tavily_client.search(query=query, search_depth="basic")
        formatted_results = ""
        for result in response.get("results", []):
            formatted_results += f"Title: {result['title']}\nURL: {result['url']}\nContent: {result['content']}\n\n"
        return formatted_results if formatted_results else "No results found."
    except Exception as e:
        return f"Error searching the web: {e}"


available_functions = {
    "get_current_time": get_current_time,
    "calculate": calculate,
    "read_file": read_file,
    "search_web": search_web,
}

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
#               AUTO TITLING
# ==========================================

# def generate_chat_title(user_message: str) -> str:
#     """Generates a short, 3-word title based on the user's first message."""
#     try:
#         response = client.chat.completions.create(
#             model="llama-3.1-8b-instant",
#             messages=[
#                 {"role": "system", "content": "You are a helpful assistant. Summarize the user's message into a concise 3-word title. Do not use quotes or punctuation."},
#                 {"role": "user", "content": user_message}
#             ],
#             max_tokens=10,
#             temperature=0.5
#         )
#         return response.choices[0].message.content.strip()
#     except Exception as e:
#         print(f"Error generating file: {e}")
#         return "New Chat"


# ==========================================
# 3. CORE AGENT LOGIC (Streaming Generator)
# ==========================================
def run_agent_stream(messages):
    """
    Takes message history, manages the LLM loop, executes tools,
    and yields UI-friendly events.
    """
    while True:
        response = client.chat.completions.create(
            model=MODEL_ID,
            messages=messages,
            tools=tools_list,
            tool_choice="auto",
            stream=True,
        )

        tool_call_buffer = {}
        final_text = ""

        # Parse the stream
        for chunk in response:
            delta = chunk.choices[0].delta

            # 1. Yield text chunks to the UI as they arrive
            if delta.content:
                final_text += delta.content
                yield {"event": "text_chunk", "content": delta.content}

            # 2. Buffer tool calls quietly
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

        # 3. Execute tools if the LLM requested them
        if tool_call_buffer:
            tool_calls_list = list(tool_call_buffer.values())
            messages.append({"role": "assistant", "tool_calls": tool_calls_list})

            for tc in tool_calls_list:
                f_name = tc["function"]["name"]

                # Tell the UI we are starting a tool
                yield {"event": "tool_start", "name": f_name}

                try:
                    f_args = json.loads(tc["function"]["arguments"])
                except json.JSONDecodeError:
                    f_args = {}

                try:
                    func = available_functions[f_name]
                    obs = func(**f_args) if f_args else func()
                except Exception as e:
                    obs = f"Error executing tool {f_name}: {str(e)}"

                # Tell the UI the tool finished
                yield {"event": "tool_result", "name": f_name, "content": str(obs)}

                # Append result to memory for the LLM
                messages.append(
                    {
                        "tool_call_id": tc["id"],
                        "role": "tool",
                        "name": f_name,
                        "content": str(obs),
                    }
                )
        else:
            # 4. If no tools were called, the turn is over!
            messages.append({"role": "assistant", "content": final_text})
            yield {"event": "done", "messages": messages}
            break
