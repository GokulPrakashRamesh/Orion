# src/dungeons_and_dragons/tools/scribe_tools.py
import uuid
import jsonschema
from neo4j import GraphDatabase
import json
import os
from dotenv import load_dotenv
from typing import Any, Dict, List

from dungeons_and_dragons.schemas.world_schema import world_schema
from dungeons_and_dragons.schemas.scene_schema import scene_schema
from dungeons_and_dragons.schemas.choice_schema import choice_schema

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "test")

# ----------------------
# Globals (current state)
# ----------------------
CURRENT_WORLD_ID: str | None = None
CURRENT_SCENE_ID: str | None = None


def _connect() -> GraphDatabase.driver:
    return GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

def _ensure_world_dict(payload: Any) -> Dict:
    if payload is None:
        raise ValueError("save_world: received None payload")

    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except Exception as e:
            raise ValueError(f"save_world: provided string is not valid JSON: {e}")

    if isinstance(payload, dict) and "world_json" in payload:
        payload = payload["world_json"]

    if isinstance(payload, dict) and "world" in payload:
        payload = payload["world"]

    if not isinstance(payload, dict):
        raise ValueError(
            f"save_world: expected dict after normalization, got {type(payload)}"
        )

    return payload

def _ensure_scene_dict(payload: Any) -> Dict:
    if payload is None:
        raise ValueError("save_scene: received None payload")

    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except Exception as e:
            raise ValueError(f"save_scene: provided string is not valid JSON: {e}")

    if isinstance(payload, dict) and "scene_json" in payload:
        payload = payload["scene_json"]

    if isinstance(payload, dict) and "scene" in payload:
        payload = payload["scene"]

    if not isinstance(payload, dict):
        raise ValueError(
            f"save_scene: expected dict after normalization, got {type(payload)}"
        )

    return payload


def _ensure_choices_list(payload: Any) -> List[Dict]:
    if payload is None:
        raise ValueError("save_choices: received None payload")

    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except Exception as e:
            raise ValueError(f"save_choices: provided string is not valid JSON: {e}")

    if isinstance(payload, dict) and "choices_json" in payload:
        payload = payload["choices_json"]

    if isinstance(payload, dict) and "choices" in payload:
        payload = payload["choices"]

    if not isinstance(payload, list):
        raise ValueError(
            f"save_choices: expected list after normalization, got {type(payload)}"
        )

    # Ensure each element is a dict
    for i, choice in enumerate(payload):
        if not isinstance(choice, dict):
            raise ValueError(
                f"save_choices: expected dict for choice at index {i}, got {type(choice)}"
            )

    return payload

def _sanitize_props(props: dict) -> dict:
    safe_props = {}
    for k, v in props.items():
        if isinstance(v, (dict, list)):
            # Store nested data as JSON string
            safe_props[k] = json.dumps(v)
        else:
            safe_props[k] = v
    return safe_props

def _save_world_impl(world: Dict) -> str:
    global CURRENT_WORLD_ID

    driver = _connect()
    with driver.session() as session:
        world_id = world.get("world_id")

        # Check if world exists
        result = session.run(
            "MATCH (w:World {world_id: $world_id}) RETURN w",
            world_id=world_id
        ) if world_id else None

        if result and result.single():
            # World exists → generate a fresh id
            world_id = str(uuid.uuid4())
            world["world_id"] = world_id

        CURRENT_WORLD_ID = world_id # Update global state

        # --- World node ---
        session.run(
            """
            MERGE (w:World {world_id: $world_id})
            SET w += $props
            """,
            world_id=world_id,
            props={
                "world_id": world.get("world_id"),
                "name": world.get("name"),
                "theme": world.get("theme"),
                "terrain_desc": world.get("terrain_desc"),
                "starting_region": world.get("starting_region"),
                "lore": world.get("lore"),
            },
        )

        # --- Factions ---
        for f in world.get("factions", []):
            fid = f"{CURRENT_WORLD_ID}.{f.get("faction_id")}"

            session.run(
                """
                MERGE (fa:Faction {faction_id: $faction_id})
                SET fa += $props
                WITH fa
                MATCH (w:World {world_id: $world_id})
                MERGE (w)-[:HAS_FACTION]->(fa)
                """,
                faction_id=fid,
                props=_sanitize_props(f),
                world_id=world_id,
            )

        # --- NPCs ---
        for npc in world.get("npc", []) + world.get("npcs", []):
            nid = f"{CURRENT_WORLD_ID}.{npc.get("npc_id")}"

            session.run(
                """
                MERGE (n:NPC {npc_id: $npc_id})
                SET n += $props
                WITH n
                MATCH (w:World {world_id: $world_id})
                MERGE (w)-[:HAS_NPC]->(n)
                """,
                npc_id=nid,
                props=_sanitize_props(npc),
                world_id=world_id,
            )

    driver.close()
    return f"World '{world.get('name')}' saved to Neo4j (world_id={world_id})."


def _save_choices_impl(choices: Dict) -> str:
    global CURRENT_SCENE_ID
    global CURRENT_WORLD_ID
    if not CURRENT_SCENE_ID:
        raise RuntimeError("No CURRENT_SCENE_ID set — save a scene first before saving choices.")

    driver = _connect()
    with driver.session() as session:
        for choice in choices:
            choice_id = choice.get("choice_id") or str(uuid.uuid4())
            choice_id = f"{CURRENT_WORLD_ID}.{CURRENT_SCENE_ID}.{choice_id}"
            choice["choice_id"] = choice_id

            # --- Merge Choice node ---
            session.run(
                """
                MERGE (c:Choice {choice_id: $choice_id})
                SET c += $props
                """,
                choice_id=choice_id,
                props={
                    "choice_id": choice_id,
                    "title": choice.get("title"),
                    "description": choice.get("description"),
                    "narration": choice.get("narration"),
                    "consequence": choice.get("consequence"),
                }
            )

            # --- Scene OFFERS Choice ---
            session.run(
                """
                MATCH (s:Scene {scene_id: $scene_id}), (c:Choice {choice_id: $choice_id})
                MERGE (s)-[:OFFERS]->(c)
                """,
                scene_id=CURRENT_SCENE_ID,
                choice_id=choice_id
            )

    driver.close()
    return f"{len(choices)} choices saved and linked to Scene (scene_id={CURRENT_SCENE_ID})."


def _save_scene_impl(scene: Dict) -> str:
    global CURRENT_SCENE_ID

    driver = _connect()
    with driver.session() as session:
        scene_id = scene.get("scene_id") or str(uuid.uuid4())
        scene_id = f"{CURRENT_WORLD_ID}.{scene_id}"
        scene["scene_id"] = scene_id

        CURRENT_SCENE_ID = scene_id # Update global state

        # Merge Scene node
        session.run(
            """
            MERGE (s:Scene {scene_id: $scene_id})
            SET s += $props
            """,
            scene_id=scene_id,
            props={
                "scene_id": scene_id,
                "title": scene.get("title"),
                "description": scene.get("description"),
                "narration": scene.get("narration")
            }
        )

        # Link NPCs that appear in this scene
        # Doesn't involve usage of existing NPCs in the world
        for npc in scene.get("npcs", []):
            npc_id = npc.get("npc_id") or str(uuid.uuid4())
            npc["npc_id"] = f"{CURRENT_WORLD_ID}.{npc_id}"
            session.run(
                """
                MERGE (n:NPC {npc_id: $npc_id})
                SET n += $props
                WITH n
                MATCH (s:Scene {scene_id: $scene_id})
                MERGE (s)-[:HAS_NPC]->(n)
                """,
                npc_id=npc_id,
                props=_sanitize_props(npc),
                scene_id=scene_id
            )

    driver.close()
    return f"Scene '{scene.get('title')}' saved (scene_id={scene_id})"


def _link_pregame_scene_to_world(scene_id: str, world_id: str) -> str:
    driver = _connect()
    with driver.session() as session:
        session.run(
            """
            MATCH (w:World {world_id: $world_id}), (s:Scene {scene_id: $scene_id})
            MERGE (w)-[:OPENS_WITH {type: 'pregame'}]->(s)
            """,
            world_id=world_id,
            scene_id=scene_id,
        )
    driver.close()
    return f"Pregame scene (scene_id={scene_id}) linked to World (world_id={world_id})."


def save_world(world_json: dict):
    world = _ensure_world_dict(world_json)

    if not world or not isinstance(world, dict):
        raise ValueError("save_world: Received empty or invalid world object")
    
    world["world_id"] = str(uuid.uuid4())

    # Validate JSON
    try:
        jsonschema.validate(instance=world, schema=world_schema)
    except jsonschema.ValidationError as e:
        raise ValueError(f"World JSON validation failed at {list(e.path)}: {e.message}")

    return _save_world_impl(world)


def save_choices(choice_json: dict):
    choices = _ensure_choices_list(choice_json)

    if not choices or not isinstance(choices, List):
        raise ValueError("save_choice: Received empty or invalid list of choice objects")
    
    for choice in choices:
        if not choice or not isinstance(choice, Dict):
            raise ValueError("save_choice: Received empty or invalid list of choice objects")

        # Validate JSON
        try:
            jsonschema.validate(instance=choice, schema=choice_schema)
        except jsonschema.ValidationError as e:
            raise ValueError(f"Choice JSON validation failed at {list(e.path)}: {e.message}")

    return _save_choices_impl(choices)


def save_scene(scene_json: dict):
    scene = _ensure_scene_dict(scene_json)

    if not scene or not isinstance(scene, dict):
        raise ValueError("save_scene: Received empty or invalid scene object")
    
    # Validate JSON
    try:
        jsonschema.validate(instance=scene, schema=scene_schema)
    except jsonschema.ValidationError as e:
        raise ValueError(f"Scene JSON validation failed at {list(e.path)}: {e.message}")

    return _save_scene_impl(scene)

def attach_pregame_scene():
    if not CURRENT_WORLD_ID:
        raise ValueError("No world_id available to attach pregame scene")
    if not CURRENT_SCENE_ID:
        raise ValueError("No scene_id available to attach pregame scene")

    return _link_pregame_scene_to_world(CURRENT_SCENE_ID, CURRENT_WORLD_ID)









# ----------------------
# NEO4J Data Accessors
# ----------------------
def get_choices_for_scene():
    global CURRENT_SCENE_ID
    driver = _connect()
    with driver.session() as session:
        results = session.run(
            """
            MATCH (s:Scene {scene_id: $scene_id})-[:OFFERS]->(c:Choice)
            RETURN DISTINCT c
            """,
            scene_id=CURRENT_SCENE_ID
        )
        choices = []
        for record in results:
            node_props = dict(record["c"].items())
            choices.append(node_props)

        print(f"\n🎯 Available Choices for Scene {CURRENT_SCENE_ID}:", choices)
        return choices


def link_choice_to_scene(choice_id, scene_id):
    driver = _connect()
    with driver.session() as session:
        # Create LEADS_TO relationship from choice -> new scene
        session.run(
            """
            MATCH (c:Choice {choice_id: $choice_id})
            MATCH (s:Scene {scene_id: $scene_id})
            MERGE (c)-[:LEADS_TO]->(s)
            """,
            choice_id=choice_id,
            scene_id=scene_id
        )