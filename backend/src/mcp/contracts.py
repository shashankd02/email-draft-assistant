MCP_RESOURCES = [
    {"uri": "memory://user/{user_id}/profile", "mode": "read_write", "scope": "scoped"},
    {"uri": "memory://user/{user_id}/threads", "mode": "read_write", "scope": "scoped"},
    {"uri": "templates://email/{template_id}", "mode": "read", "scope": "global"},
    {"uri": "policy://safety/ruleset", "mode": "read", "scope": "global"},
]

MCP_TOOLS = [
    {"name": "tool.search_web", "signature": "(query, recency_days)", "returns": "citations + confidence"},
    {"name": "tool.voice.transcribe", "signature": "(audio_stream)", "returns": "transcript + diarization"},
    {"name": "tool.voice.speak", "signature": "(text, persona_id)", "returns": "audio"},
    {"name": "tool.memory.upsert_profile", "signature": "(fields)", "returns": "versioned profile state"},
]
