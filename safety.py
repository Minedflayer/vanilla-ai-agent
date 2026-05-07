# safety.py


# Any tool listed here will execute immediately without asking the user.
# AUTO_APPROVE_TOOLS = [
#     "get_current_time",
#     "calculate",
#     "search_web",  # Let's assume searching the web is safe
# ]

# # Tools listed here will trigger the security intercept.
# # (Imagine you eventually add a tool called "delete_file" or "send_email")
# DANGEROUS_TOOLS = [
#     "read_file",  # Reading files might expose sensitive local data
#     "delete_file",
#     "execute_code",
# ]


# def get_human_approval(tool_name: str, tool_args: dict) -> bool:
#     """
#     Checks if a tool is safe to auto-run. If it is dangerous or unknown,
#     it interrupts the execution flow to ask the user for explicit permission.
#     """

# # The Fast-Pass (Auto-Approve)
# if tool_name in AUTO_APPROVE_TOOLS:
#     print(f"\n⚡ [Auto-Approve]: Executing safe tool '{tool_name}'...")
#     return True

# # The Security Intercept (Require Human Approval)
# print(
#     f"\n🛑 [SECURITY INTERCEPT]: The AI is attempting to execute a restricted tool."
# )
# print(f"   Tool: {tool_name}")
# print(f"   Arguments: {tool_args}")

# while True:
#     choice = input("   Allow this execution? (y/n): ").strip().lower()
#     if choice in ["y", "yes"]:
#         return True
#     elif choice in ["n", "no"]:
#         return False
#     else:
#         print("   Invalid input. Please type 'y' or 'n'.")
