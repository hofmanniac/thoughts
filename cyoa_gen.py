import json
import random
from typing import Dict, Optional
from thoughts.interfaces.llm import LLM
from thoughts.interfaces.messaging import HumanMessage

llm = LLM()
difficulty = 0.5  # 0.0 = always success, 1.0 = always failure, adjust as needed

success_limit = 3
success_count = [0]  # Use a list for mutability in recursion

def should_end_branch(depth: int, base_chance: float = 0.08, growth: float = 0.10, max_depth: int = 20) -> bool:
    if depth >= max_depth:
        return True
    probability = min(base_chance + growth * (depth - 1), 0.98)
    return random.random() < probability

def decide_leaf_result(depth: int, difficulty: float, success_count: list, success_limit: int) -> str:
    # Only allow success if we haven't hit the limit, and only at higher depths
    min_success_depth = 8  # Only allow success after this depth
    success_chance = 0.05  # Very low chance per leaf
    if depth >= min_success_depth and success_count[0] < success_limit and random.random() < success_chance * (1 - difficulty):
        success_count[0] += 1
        return "success"
    return "failure"

def generate_node(goal: str, prev_summary: str, player_choice: Optional[str], state: Dict[str, str], depth: int, difficulty: float, max_depth: int = 20) -> dict:
    is_leaf = should_end_branch(depth, max_depth=max_depth)
    node_result = None
    ending = ""
    if is_leaf:
        node_result = decide_leaf_result(depth, difficulty, success_count, success_limit)
        ending = f"\nThe adventure ends in {node_result.upper()}."

    prompt = ""
    prompt += "You are writing an immersive choose-your-own-adventure story.\n\n"
    prompt += f"Overall Goal: {goal}\n\n"
    prompt += f"Plot Summary: {prev_summary}\n\n"
    prompt += f"Player Choice: {player_choice or 'None'}\n\n"
    prompt += f"Player State: {state}\n\n"
    prompt += "Write:\n"
    if is_leaf:
        prompt += f"- An ending scene for the adventure where the story ends in {node_result.upper()}.\n"
    else:
        prompt += "- A short narrative (1-2 paragraphs) setting up the scene or describing the situation after the player's choice\n"
        prompt += "- Offer 2-3 meaningful choices the player can make next, aligned with the goal and expanding the plot.\n"
    prompt += "\nRespond in JSON:\n"
    prompt += "{\n"
    prompt += f"\"content\": \"Narrative text here...{ending}\",\n"
    prompt += "\"summary\": \"A brief summary of the plot so far.\",\n"
    if not is_leaf:
        prompt += "\"choices\": [\"Choice 1\", \"Choice 2\", \"Choice 3\"]\n"
    prompt += "}\n"

    messages = [HumanMessage(content=prompt)]
    response = llm.invoke(messages, stream=True, json=True)
    parsed = json.loads(response.content)

    if is_leaf or not parsed.get("choices"):
        parsed["outcomes"] = []
        parsed["result"] = node_result
        return parsed

    parsed["outcomes"] = []
    for choice in parsed.get("choices", []):
        print(f"Generating outcome for choice: {choice}")
        print()
        child_node = generate_node(
            goal=goal,
            prev_summary=parsed["summary"],
            player_choice=choice,
            state=state,
            depth=depth + 1,
            difficulty=difficulty,
            max_depth=max_depth
        )
        parsed["outcomes"].append({
            "choice": choice,
            "node": child_node
        })
    return parsed

def generate_story():
    print("Generating Story...")

    global success_count
    success_count = [0]  # Reset for each story

    root_node = generate_node(
        goal="Explore the pirate ship and find the treasure",
        prev_summary="You have boarded a pirate ship in search of hidden treasure. The ship is old and creaky, with dark corners and mysterious sounds echoing through the halls. You must navigate through the ship, making choices that will lead you closer to the treasure or into danger.",
        player_choice=None,
        state={"health": "100", "points": "0"},
        depth=1,
        difficulty=difficulty,
        max_depth=10  # High cap to prevent infinite recursion
    )
    print(json.dumps(root_node, indent=2))
    json.dump(root_node, open("story.json", "w"), indent=2)

generate_story()


    # llm = LLM()

    # def call_llm(prompt: str) -> str:
    #     messages = [HumanMessage(content=prompt)]
    #     response = llm.invoke(messages, stream=True, json=True)
    #     parsed = json.loads(response.content)