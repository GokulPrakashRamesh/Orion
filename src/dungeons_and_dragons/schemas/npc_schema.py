npc_schema = {
    "type": "object",
    "properties": {
        "npc_id": {"type": "string"},
        "name": {"type": "string"},
        "desc": {"type": "string"},
        "faction": {
            "type": "object",
            "properties": {
                "faction_id": {"type": "string"},
                "name": {"type": "string"}
            },
            "required": ["faction_id", "name"],
            "additionalProperties": True 
        },
        "characteristics": {
            "type": "array",
            "items": {"type": "string"}
        }
    },
    "required": ["npc_id", "name"],
    "additionalProperties": True 
}