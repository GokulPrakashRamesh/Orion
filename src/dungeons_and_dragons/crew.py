from crewai import Agent, Crew, Process, Task
from crewai.tools import tool
from crewai.project import CrewBase, agent, task, crew
from crewai.agents.agent_builder.base_agent import BaseAgent

from dungeons_and_dragons.tools.scribe_tools import save_world

from typing import List

@CrewBase
class DungeonMasterCrew():
    """Multi-agent AI Dungeon Master with structured crews for each stage"""

    agents: List[BaseAgent]
    tasks: List[Task]

    # === Agents ===
    @agent
    def world_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['world_agent'], 
            verbose=True
        )

    @agent
    def npc_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['npc_agent'], 
            verbose=True
        )

    @agent
    def npc_setup(self) -> Agent:
        return Agent(
            config=self.agents_config['npc_setup'], 
            verbose=True
        )

    @agent
    def dungeon_master(self) -> Agent:
        return Agent(
            config=self.agents_config['dungeon_master'],
            verbose=True
        )
    
    @agent
    def scribe_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['scribe_agent'],
            verbose=True,
            llm_config={
                "temperature": 0.2
            }
        )
    
    @agent
    def choice_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['choice_agent'],
            verbose=True
        )

    # === Tasks ===
    @task
    def setup_world(self) -> Task:
        return Task(config=self.tasks_config['setup_world'])
    
    @task
    def structure_world(self) -> Task:
        return Task(config=self.tasks_config['structure_world'])

    @task
    def pregame_scene(self) -> Task:
        return Task(config=self.tasks_config['pregame_scene'])
    
    @task
    def pregame_choices(self) -> Task:
        return Task(config=self.tasks_config['pregame_choices'])
    
    @task
    def resolve_player_choice(self) -> Task:
        return Task(config=self.tasks_config['resolve_player_choice'])
    
    @task
    def progress_scene(self) -> Task:
        return Task(config=self.tasks_config['progress_scene'])
    
    @task
    def progress_choices(self) -> Task:
        return Task(config=self.tasks_config['progress_choices'])
    
    @task
    def summarize_story_progression(self) -> Task:
        return Task(config=self.tasks_config['summarize_story_progression'])
    
    @task
    def generate_plot_skeleton(self) -> Task:
        return Task(config=self.tasks_config['generate_plot_skeleton'])
    
    @task
    def overarching_plot(self) -> Task:
        return Task(config=self.tasks_config['overarching_plot'])

    @task
    def ending(self) -> Task:
        return Task(config=self.tasks_config['ending'])

    @task
    def npc_interaction(self) -> Task:
        return Task(config=self.tasks_config['npc_interaction'])

    @task
    def role_assignment(self) -> Task:
        return Task(config=self.tasks_config['role_assignment'])
    
    @task
    def structure_scene(self) -> Task:
        return Task(config=self.tasks_config['structure_scene'])
    
    @task
    def structure_choice(self) -> Task:
        return Task(config=self.tasks_config['structure_choice'])
    

    # === Crews ===
    @crew
    def world_setup_crew(self) -> Crew:
        """Handles world creation"""
        return Crew(
            agents=[self.world_agent(), self.scribe_agent()],
            tasks=[self.setup_world(), self.structure_world()],
            process=Process.sequential,
            verbose=True,
        )
    
    @crew
    def pregame_scene_setup_crew(self) -> Crew:
        """Handles initial scene setup"""
        return Crew(
            agents=[self.dungeon_master(), self.scribe_agent()],
            tasks=[self.pregame_scene(), self.structure_scene()],
            process=Process.sequential,
            verbose=True,
        )
    
    @crew
    def pregame_choices_setup_crew(self) -> Crew:
        """Handles initial choices setup"""
        return Crew(
            agents=[self.dungeon_master(), self.scribe_agent()],
            tasks=[self.pregame_choices(), self.structure_choice()],
            process=Process.sequential,
            verbose=True,
        )
    
    @crew
    def player_interaction_crew(self) -> Crew:
        """Handles player actions, outcomes, and integrates story progression"""
        return Crew(
            agents=[self.choice_agent()],
            tasks=[self.resolve_player_choice()],
            process=Process.sequential,
            verbose=True,
        )
    
    @crew
    def story_scene_progression_crew(self) -> Crew:
        """Handles progression of storylines and side quests"""
        return Crew(
            agents=[self.dungeon_master(), self.scribe_agent()],
            tasks=[self.progress_scene(), self.structure_scene()],
            process=Process.sequential,
            verbose=True,
        )
    
    @crew
    def story_choices_progression_crew(self) -> Crew:
        """Handles branching of storylines and side quests"""
        return Crew(
            agents=[self.dungeon_master(), self.scribe_agent()],
            tasks=[self.progress_choices(), self.structure_choice()],
            process=Process.sequential,
            verbose=True,
        )
    
    @crew
    def story_summary_crew(self) -> Crew:
        """Handles summarization of story progression"""
        return Crew(
            agents=[self.dungeon_master()],
            tasks=[self.summarize_story_progression()],
            process=Process.sequential,
            verbose=True,
        )
    
    @crew
    def story_convergence_crew(self) -> Crew:
        """Handles convergence of storylines to structure ending"""
        return Crew(
            agents=[self.dungeon_master()],
            tasks=[self.generate_plot_skeleton()],
            process=Process.sequential,
            verbose=True,
        )
    
    @crew
    def story_ending_crew(self) -> Crew:
        """Handles overarching plot and story resolution"""
        return Crew(
            agents=[self.dungeon_master()],
            tasks=[self.overarching_plot(), self.ending()],
            process=Process.sequential,
            verbose=True,
        )

    @crew
    def npc_interactions_crew(self) -> Crew:
        """Handles NPC creation, role assignment, and interactions"""
        return Crew(
            agents=[self.npc_agent(), self.npc_setup()],
            tasks=[self.role_assignment(), self.npc_interaction()],
            process=Process.sequential,
            verbose=True,
        )
