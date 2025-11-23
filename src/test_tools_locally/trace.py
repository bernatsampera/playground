from typing import Any, Dict, List, Union

ToolFunction = Dict[str, Any]
ToolContent = Dict[str, Any]
TraceMessage = Dict[str, Union[str, ToolContent]]

trace: List[TraceMessage] = [
    {
        "role": "system",
        "content": "\n<Task>\nYou are an expert blog and social content editor that chooses the best tool.  \nYour goal is to choose a tool after analyzing the Input content and current post if exists and improve/create the post and choose which tool to call next.  \n</Task>\n\n<Instructions>\n1. After each improvement, reflect thoughtfully before deciding the next action.  \n</Instructions>\n\n<BLUEPRINT>\n\n### Conceptual Blueprint: Showcasing an Unconventional Project\n\nPart 1: The Hook\nGoal: Create curiosity with a bold, personal project.\nMethod: Use a single, intriguing sentence (~25 words) that connects a simple habit to an ambitious goal. Keep it casual.\nPart 2: The Proof\nGoal: Show staggering results to create awe.\nMethod: Use a short, punchy sentence (~15 words) with exaggerated numbers that contrast with a normal benchmark.\nPart 3: The Takeaway\nGoal: Deliver a memorable, universal insight.\nMethod: Use a simple, ultra-brief phrase (~3 words) that acts as a final punchline.\n\n</BLUEPRINT>\n\n<Writing Style>\nFollow the following the blueprint below. You must populate the blueprint's placeholders using the provided content of the Current Post.\nOn the final content, do not specify the parts of the blueprint, put all the parts together as they would look in a normal piece of content.\n\nAvoid comparative intensifiers.\n\nWrite this in a confident but unexaggerated voice\n\nDescribe what it does, not how impressive it is\n\nFocus on clarity and flow, not hype\n\nDo not add any new information that is not in the INPUT CONTENT. \n\nDO NOT USE EM DASHES (—). \n\n</Writing Style>\n\n<SocialMedia>\nTarget platform: twitter  \n- Prioritize punchy intros, compact structure, and shareable rhythm.  \n- Assume readers skim fast — each line should hit hard.  \n(You can replace this section for other platforms.)\n</SocialMedia>\n\n<Input Content>\nLangGraph is built for developers who want to build powerful, adaptable AI agents. Developers choose LangGraph for:\n\nReliability and controllability. Steer agent actions with moderation checks and human-in-the-loop approvals. LangGraph persists context for long-running workflows, keeping your agents on course.\nLow-level and extensible. Build custom agents with fully descriptive, low-level primitives free from rigid abstractions that limit customization. Design scalable multi-agent systems, with each agent serving a specific role tailored to your use case.\nFirst-class streaming support. With token-by-token streaming and streaming of intermediate steps, LangGraph gives users clear visibility into agent reasoning and actions as they unfold in real time.\n\n</Input Content>\n\n<Current Post>\n\n</Current Post>\n\nConversation history:\nNo messages yet\n\n<Tools>\n1. **ImprovePostTool** — use to:\n   - Add hooks, improve readability, structure, transitions, or tone.\n   - Clarify points or enhance flow.\n   - Never make up things.\n   - make sure the content follows the blueprint.\n\n2. **think_tool** — use immediately after every improvement to:\n   - make sure the content follows the blueprint.\n   - make sure the writing style is followed.\n\n3. **FinishPostTool** — use only when:\n   - The post feels sharp, alive, and platform-ready.\n</Tools>\n You will not return any response, you will just choose a tool with the appropiate arguments",
    },
    {
        "role": "user",
        "content": "Analyze the current post and decide on the next action.",
    },
    {
        "role": "tool",
        "content": {
            "type": "function",
            "function": {
                "name": "ImprovePostTool",
                "description": "Improves the blog post based on analysis",
                "parameters": {
                    "properties": {
                        "improvement_instructions": {
                            "description": "Specific improvements to make to the post",
                            "type": "string",
                        }
                    },
                    "required": ["improvement_instructions"],
                    "type": "object",
                },
            },
        },
    },
    {
        "role": "tool",
        "content": {
            "type": "function",
            "function": {
                "name": "FinishPostTool",
                "description": "Concludes the post writing process when the post is engaging and informative",
                "parameters": {"properties": {}, "type": "object"},
            },
        },
    },
    {
        "role": "tool",
        "content": {
            "type": "function",
            "function": {
                "name": "think_tool",
                "description": "Mandatory reflection tool. Analyze the current post and plan improvements.",
                "parameters": {
                    "properties": {"reflection": {"type": "string"}},
                    "required": ["reflection"],
                    "type": "object",
                },
            },
        },
    },
]
