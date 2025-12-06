scene_schema = {
    "type": "object",
    "properties": {
        "scene_id": {"type": "string"},
        "title": {"type": "string"},
        "description": {"type": "string"},
        "narration": {"type": "string"},
    },
    "required": ["scene_id", "title", "description", "narration"],
    "additionalProperties": True
}