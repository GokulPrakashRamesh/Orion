world_schema = {
    "type": "object",
    "properties": {
        "world_id": {"type": "string"},
        "name": {"type": "string"},
        "theme": {"type": "string"},
        "terrain_desc": {"type": "string"},
        "starting_region": {"type": "string"},
        "factions": {
            "type": "array",
            "items": {"$ref": "#/definitions/faction"}
        },
        "npcs": {
            "type": "array",
            "items": {"$ref": "#/definitions/npc"}
        },
        "lore": {"type": "string"}
    },
    "required": ["world_id", "name", "theme", "terrain_desc", "starting_region", "lore"],
    "optional": ["factions", "npcs"],
    "definitions": {
        "faction": {
            "type": "object",
            "properties": {
                "faction_id": {"type": "string"},
                "name": {"type": "string"}
            },
            "required": ["faction_id", "name"],
            "additionalProperties": True 
        },
        "npc": {
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
    }
}