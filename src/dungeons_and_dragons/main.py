import json
import random
from dotenv import load_dotenv
from dungeons_and_dragons.crew import DungeonMasterCrew
from dungeons_and_dragons.tools.scribe_tools import attach_pregame_scene, save_world, save_scene, save_choices, get_choices_for_scene, link_choice_to_scene

load_dotenv()

dm = DungeonMasterCrew()

# Initialize crews
world_setup_crew = dm.world_setup_crew()
pregame_scene_setup_crew = dm.pregame_scene_setup_crew()
pregame_choices_setup_crew = dm.pregame_choices_setup_crew()
player_interaction_crew = dm.player_interaction_crew()
story_scene_progression_crew = dm.story_scene_progression_crew()
story_choices_progression_crew = dm.story_choices_progression_crew()
story_summary_crew = dm.story_summary_crew()
story_convergence_crew = dm.story_convergence_crew()
npc_interactions_crew = dm.npc_interactions_crew()
story_ending_crew = dm.story_ending_crew()


import json
import re

def crewOutputToJSON(crew_output):
    """Utility to convert Crew output to JSON dict"""
    output = crew_output.raw
    
    if isinstance(output, str):
        text = output.strip()

        # Try direct JSON parse first
        try:
            return json.loads(text)
        except Exception:
            pass  

        # If it failed, look for a JSON block inside triple backticks
        match = re.search(r"```json(.*?)```", text, re.DOTALL)
        if match:
            json_block = match.group(1).strip()
            try:
                return json.loads(json_block)
            except Exception as e:
                raise ValueError(f"Failed to parse JSON block: {e}\nExtracted block:\n{json_block}")

        # Fallback: try to extract any {...} JSON-like structure
        match = re.search(r"(\{.*\})", text, re.DOTALL)
        if match:
            json_block = match.group(1).strip()
            try:
                return json.loads(json_block)
            except Exception as e:
                raise ValueError(f"Failed to parse fallback JSON: {e}\nExtracted block:\n{json_block}")

        raise ValueError(f"No valid JSON found in Crew output:\n{text}")

    return output


# =========================
# Step 1: Setup the Game
# =========================
def setup_game():
    print("🎲 Setting up the world...")

    structured_world = world_setup_crew.kickoff()
    print("\n🌍 World structured:", structured_world.raw)
    world_data = crewOutputToJSON(structured_world)

    save_world(world_data)

    pregame_scene = pregame_scene_setup_crew.kickoff()
    scene_data = crewOutputToJSON(pregame_scene)

    save_scene(scene_data)
    attach_pregame_scene()

    choices = pregame_choices_setup_crew.kickoff()
    choices_data = crewOutputToJSON(choices)

    save_choices(choices_data)

    print("\n🌍 Opening Scene:", scene_data["narration"])
    print("\n🌍 Player Choices:", choices)

    return structured_world, pregame_scene


# =========================
# Step 2: Main Game Loop
# =========================
def run():
    structured_world, pregame_scene = setup_game()

    # Track state
    overarching_plot = None
    current_story_progression = f"The generated world is described as: {str(structured_world)} and opens with: {str(pregame_scene)}"
    scene_count = 1

    while True:
        player_action = player_action = input("\n➡️ What does your character do? (or type 'quit' to exit): ")
        if player_action.lower() == "quit":
            print("👋 Thanks for playing!")
            break

        choices = get_choices_for_scene()

        matched_choice_output = player_interaction_crew.kickoff(inputs={
            "player_action": player_action,
            "available_choices": choices
        })
        matched_choice = crewOutputToJSON(matched_choice_output)

        if matched_choice["status"] == "retry":
            print("❌ Invalid action. Please choose a valid option.")
            continue

        if matched_choice["status"] == "success":
            current_story_progression += f"\nPlayer chose to do: {player_action} for choice: {matched_choice}\n" # Update progression

            choice_id = matched_choice["choice"]["choice_id"]

            # Generate the next scene
            next_scene_output = story_scene_progression_crew.kickoff(inputs={
                "current_story_progression": current_story_progression,
                "choice": matched_choice_output.raw,
                "player_action": player_action
            })
            next_scene_data = crewOutputToJSON(next_scene_output)

            # Save next scene + link via LEADS_TO
            save_scene(next_scene_data)
            link_choice_to_scene(choice_id, next_scene_data["scene_id"])

            current_story_progression += f"\nThe previous choice led to the following scene: {next_scene_data}\n" # Update progression

        next_choices_output = story_choices_progression_crew.kickoff(inputs={
            "current_story_progression": current_story_progression,
            "scene_context": next_scene_data
        })
        next_choices_data = crewOutputToJSON(next_choices_output)

        save_choices(next_choices_data)

        # Update state
        scene_count += 1

        # Every 2 scenes, update the current story progression with a summary of what happened in the plot so far.
        if scene_count % 2 == 0:
            summary = story_summary_crew.kickoff(inputs={
                "current_story_progression": current_story_progression
            })
            current_story_progression = summary.raw  # Refresh progression with summary
            print("\n📝 Story Summary Update:", summary)

        # Check condition for generating plot skeleton
        if scene_count >= 5:
            plot_skeleton = story_convergence_crew.kickoff(inputs={
                "current_story_progression": current_story_progression
            }).raw
            print("\n🧩 Plot Skeleton Update:", plot_skeleton)

        # Display the scene and its corresponding choices
        print("\n🌍 Scene:", next_scene_data["narration"])
        print("\n🌍 Player Choices:", next_choices_output)


        # player_action = input("\n➡️ What does your character do? (or type 'quit' to exit): ")
        # current_story_progression += "Player chose: " + player_action
        # if player_action.lower() == "quit":
        #     print("👋 Thanks for playing!")
        #     break

        # # Decide whether next step is branching or an event
        # scene_type = random.choice(["choice", "event"])

        # if scene_type == "choice":
        #     scene = story_progression_crew.kickoff(
        #         inputs={"input_text": f"Player chose {player_action}. Continue the story with 3 new branching options."}
        #     )

        #     side_quest = ""
        #     if(random.randint(1,10) == random.randint(1,10)):
        #         # Side quest enrichment
        #         side_quest = story_progression_crew.kickoff(
        #             inputs={"input_text": "Suggest a fun but optional side-quest linked to the current scene."}
        #         )

        #     current_story_progression += str(scene) + str(side_quest)
        #     print("\n🌍 New Scene:", scene, side_quest)

        # else:
        #     dice_roll = random.randint(1, 20)
        #     print(f"\n🎲 You rolled a {dice_roll}!")

        #     if dice_roll <= 7:
        #         outcome = player_interaction_crew.kickoff(
        #             inputs={"input_text": f"Dice roll {dice_roll}. Narrate a failure or complication."}
        #         )
        #     elif dice_roll <= 14:
        #         outcome = player_interaction_crew.kickoff(
        #             inputs={"input_text": f"Dice roll {dice_roll}. Reveal lore or hidden truth of the story so far."}
        #         )
        #     else:
        #         print("\n🧙 NPC approaches...")
        #         outcome = npc_interactions_crew.kickoff(
        #             inputs={"input_text": f"Dice roll {dice_roll}. Trigger an NPC encounter that changes the story direction. Roleplay the important NPC interaction with the player."}
        #         )

        #     print(outcome)
        #     current_story_progression += str(outcome)

        # # Overarching plot reveal
        # scene_count += 1
        # if scene_count == 3 and not overarching_plot:
        #     overarching_plot = story_ending_crew.kickoff(
        #         inputs={"input_text": f"Based on current story progression and context {current_story_progression}, define a central overarching plot that will guide the rest of the story towards a satisfying ending."}
        #     )
        #     print("\n🌌 The overarching plot is revealed:", overarching_plot)

        # # Endgame trigger
        # if scene_count >= 7 and overarching_plot:
        #     ending = story_ending_crew.kickoff(
        #         inputs={"input_text": f"Conclude the story based on the overarching plot: {overarching_plot} and the current story progression: {current_story_progression}. Ensure a satisfying resolution."}
        #     )
        #     print("\n🏆 Story Ending:", ending)
        #     print("👋 Thanks for playing! The adventure is complete.")
        #     break


if __name__ == "__main__":
    run()
