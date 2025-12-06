choice_schema = {
    "type": "object",
    "properties": {
        "choice_id": {"type": "string"},
        "title": {"type": "string"},
        "description": {"type": "string"},
        "narration": {"type": "string"},
        "consequence": {"type": "string"}
    },
    "required": ["choice_id", "title", "description", "narration", "consequence"],
    "additionalProperties": True
}