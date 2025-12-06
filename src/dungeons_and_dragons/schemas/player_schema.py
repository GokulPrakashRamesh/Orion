player_schema = {
    "type": "object",
    "properties": {
        "id": {"type": "string"},
        "display_name": {"type": "string"},
        "character": {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "name": {"type": "string"},
                "class": {"type": "string"},
                "abilites": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "characteristics": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            },
            "required": ["id", "name", "characteristics"],
            "optional": ["class", "abilities"]
        }
    },
    "required": ["id", "display_name", "character"]
}