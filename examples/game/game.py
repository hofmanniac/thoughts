import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from thoughts.engine import Context, PipelineExecutor
from thoughts.operations.thought import Thought
from thoughts.operations.console import ConsoleReader, ConsoleWriter
from thoughts.operations.prompting import ContinueContext, IncludeFile, IncludeHistory, IncludeItem, Instruction, PromptConstructor, Role, IncludeContext, StartInstruction

# create a new context - a container for all the data associated with the current state of the game
context = Context(content_path="game")

# during executinon, you can insert items from memory
# this is a flexible way to bring in content that may change throughout the execution cycle
# here we are setting the context item "Quest Overview" to a specific value to illustrate how this works
# we'll use this in the pipeline below
context.set_item("Quest Overview", 
    "The player embarks on their journey by seeking out a legendary airship captain who is rumored to possess a map that reveals the first clue to the location of the fabled island of Elysium. This quest will involve tracking down the captain, gaining his trust, and ultimately obtaining the map.")

# a pipeline is a sequence of operations that are executed in order
pipeline = PipelineExecutor(nodes=[
    
    # this Thought will handle the main game loop
    Thought("Main Game", train=PromptConstructor([

        # begin your prompt with a Role, which will represent the persona of the Thought
        Role("You are a game master for a solo RPG game based in a Steampunk universe."),

        # you can append additional contxt to the Role directly, for example via text
        # use this for background information, additional instructions, or other information the role needs to do its job
        "Overall Campaign:\nThe world is a series of floating islands connected by vast airships and dirigibles. The player, an intrepid explorer and adventurer, is on a quest to find the legendary island of Elysium, rumored to hold untold treasures and ancient technologies.",

        # you can also use a ContextAppender, which gives you a few more options to control the content
        IncludeContext("Current Quest:\nThe current quest is called 'The Captain's Map'." ),

        # ContextAppender also supports providing a title and content separately, which is a common pattern
        IncludeContext("Quest Goal", 
        "Obtain a lost map from a retired airship captain that reveals the first clue to Elysium's location."),

        # then use the 'from_item' parameter to pull in the content from memory
        IncludeItem("Quest Overview"),

        # you can also use use list values for the context value
        IncludeContext("Quest Objectives", [
            "- Investigate Rumors: Gather information about the retired captain's whereabouts.",
            "- Locate the Captain: Find the captain in a hidden, secluded location.",
            "- Gain Trust: Complete a task or series of tasks to earn the captain's trust.",
            "- Obtain the Map: Secure the map from the captain, either through persuasion, trade, or other means."]),

        # here you can grab content from a file to add to the context
        IncludeFile("scene.txt"),

        # you can also use a ContextAppender to pull in content from memory
        # this value is set in the Progress Summary Thought below
        IncludeItem("Progress Summary", key="Summary"), 

        # this Instruction will prompt the player to take an action
        # it only runs when the Thought is executed on subsequent runs, not the first time
        ContinueContext("In a single paragraph, describe what happens in the very next turn based on the player's action. Only describe the effects on the environment and NPCs, do not make up any decisions or actions on behalf of the player. Use the second person voice. Always end with asking what the player wants to do next."),

        # this appends the history of the conversation to the context
        IncludeHistory(4),

        # this Instruction will prompt the player to take an action
        # it only runs when the Thought is first executed, not on subsequent runs
        StartInstruction("This is the beginning of the game. In 1-2 paragraphs, introduce the player to the overall campaign and quest goal. Do not give away the quest overview or objectives yet. Bring the player into the story through an epic-style introduction, describe the current scene, and then ask the play what they would like to do next. Always use the second person voice.")
    ])), 
    
    # this operation will write the AI's response to the console
    ConsoleWriter(typing_speed=0.01), 
    
    # this Thought will summarize the game state
    # it will run every 4 turns, and is used above in the main game loop Progress Summary context
    Thought("Summarizer", run_every=4, save_into="Summary", train=PromptConstructor([
        Role("You are a game master for a solo RPG game based in a Steampunk universe."),
        IncludeHistory(8), 
        Instruction(
        "Summarize what has happened in the game so far based on the above conversation. Create a list of simple sentences that represent a chronological list of events and accomplishments. State the information in the past tense. Format the results as non-numbered bulleted list with no other introduction or commentary.")
    ])), 

    # this operation will read the player's input from the 
    # the message will be stored in the context message history and used in the next iteration of the loop
    ConsoleReader("YOU:")
    
    ])

# set the pipeline to loop so it runs indefinitely
pipeline.loop = True

# run the pipeline!
pipeline.execute(context)