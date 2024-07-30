
from thoughts.operations.console import ConsoleReader, ConsoleWriter
from thoughts.operations.memory import MemoryKeeper, MemoryRetriever
from thoughts.operations.prompting import PromptRunner, PromptConstructor, StaticPromptLoader
from thoughts.engine import Context
from thoughts.engine import PipelineExecutor

context = Context(prompt_path="game")

game_master = StaticPromptLoader("game-master")
campaign = StaticPromptLoader("campaign")
quest = StaticPromptLoader("quest")
scene = StaticPromptLoader("scene")
intro = StaticPromptLoader("intro-game")
reader = ConsoleReader("YOU:")
writer = ConsoleWriter()

# introduce the game
constructor = PromptConstructor([game_master, campaign, quest, scene, intro])
runner = PromptRunner(prompt_constructor=constructor)
pipeline = PipelineExecutor([runner, writer], context)
pipeline.execute()

# main game loop
manage = StaticPromptLoader("manage-game")
summary = MemoryRetriever("summary", "Progress Summary")
constructor = PromptConstructor([game_master, campaign, quest, scene, summary, manage])
runner = PromptRunner(prompt_constructor=constructor, num_chat_history=4)

# summarizer
summary_prompt = PromptConstructor([StaticPromptLoader("summarize-progress")])
summarizer = PromptRunner(
    prompt_constructor=summary_prompt, num_chat_history=8, run_every=4, append_history=False, run_as_message=True, stream=False)
memory_keeper = MemoryKeeper()

# run the game
pipeline = PipelineExecutor([reader, runner, writer, summarizer, memory_keeper], context, loop=True)
pipeline.execute()