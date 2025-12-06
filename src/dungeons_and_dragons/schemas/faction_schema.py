faction_schema = {
    "type": "object",
    "properties": {
        "faction_id": {"type": "string"},
        "name": {"type": "string"}
    },
    "required": ["faction_id", "name"],
    "additionalProperties": True 
}