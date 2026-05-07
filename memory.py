# memory.py


def enforce_memory_limit(messages, max_messages=10):
    """
    Ensures the agent's memory doesn't exceed a certain length.
    Always preserves the System Prompt (index 0).
    """
    # If we are under the limit, just return to the list-as-is
    if len(messages) <= max_messages:
        return messages

    print(
        f"\n🧹 [Memory Manager]: Conversation exceeded {max_messages} messages. Cleaning up old history..."
    )

    # Save system prompt
    system_prompt = messages[0]

    # Grab recent message
    recent_messages = messages[-max_messages:]

    # 3. CRITICAL SAFETY CHECK:
    # We cannot accidentally delete an AI tool request but keep the tool output.
    # If the first message in our new "recent" list is a "tool" result,
    # or an assistant "tool_call", we delete it to prevent API crashes.
    while len(recent_messages) > 0 and recent_messages[0].get("role") == "tool":
        recent_messages.pop(0)

    while len(recent_messages) > 0 and "tool_calls" in recent_messages[0]:
        recent_messages.pop(0)

    # Glue the system prompt back to the clean recent messages
    return [system_prompt] + recent_messages
