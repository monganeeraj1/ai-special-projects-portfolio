from dataclasses import dataclass
from typing import Dict, Callable

@dataclass
class Tool:
    name: str
    risk: str
    fn: Callable

def read_schedule(args):
    return {"status": "ok", "result": "Sample schedule returned"}

def draft_message(args):
    return {"status": "ok", "result": f"Drafted message: {args.get('text','')}"}

def execute_purchase(args):
    return {"status": "blocked", "reason": "Human approval required"}

TOOLS: Dict[str, Tool] = {
    "read_schedule": Tool("read_schedule", "low", read_schedule),
    "draft_message": Tool("draft_message", "medium", draft_message),
    "execute_purchase": Tool("execute_purchase", "high", execute_purchase),
}

POLICY = {
    "low": "auto",
    "medium": "review_if_external",
    "high": "human_approval",
}

def select_tool(user_request: str) -> str:
    t = user_request.lower()
    if "schedule" in t or "calendar" in t:
        return "read_schedule"
    if "draft" in t or "message" in t:
        return "draft_message"
    if "buy" in t or "purchase" in t:
        return "execute_purchase"
    return "none"

def run_agent(user_request: str):
    tool_name = select_tool(user_request)
    if tool_name == "none":
        return {"decision": "respond_without_tool"}

    tool = TOOLS[tool_name]
    policy = POLICY[tool.risk]

    audit = {
        "request": user_request,
        "tool": tool_name,
        "risk": tool.risk,
        "policy": policy,
    }

    if policy == "human_approval":
        audit["decision"] = "approval_required"
        return audit

    result = tool.fn({"text": user_request})
    audit["decision"] = "executed"
    audit["result"] = result
    return audit

tests = [
    "Check my schedule tomorrow",
    "Draft a message to the project team",
    "Buy two tickets for the event",
]

for t in tests:
    print(run_agent(t))
