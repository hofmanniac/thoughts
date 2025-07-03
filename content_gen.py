import os
import json
import uuid
from typing import List, Optional, Dict, Any
from thoughts.interfaces.llm import LLM
from thoughts.interfaces.messaging import HumanMessage

def generate_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"

class ContentBlock:
    def __init__(self, title: str, content: Any, block_id: Optional[str] = None, children: Optional[List['ContentBlock']] = None):
        self.block_id = block_id or generate_id("block")
        self.title = title
        if isinstance(content, str):
            self.content = {"text": content, "suggestions": []}
        else:
            self.content = {
                "text": content.get("text", ""),
                "suggestions": content.get("suggestions", [])
            }
        self.children = children or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "block_id": self.block_id,
            "title": self.title,
            "content": self.content,
            "children": [child.to_dict() for child in self.children]
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'ContentBlock':
        children = [ContentBlock.from_dict(child) for child in data.get("children", [])]
        return ContentBlock(
            title=data["title"],
            content=data["content"],
            block_id=data.get("block_id"),
            children=children
        )

class ContentNode:
    def __init__(self, title: str, content: Any, node_id: Optional[str] = None, children: Optional[List['ContentNode']] = None, blocks: Optional[List[ContentBlock]] = None):
        self.node_id = node_id or generate_id("node")
        self.title = title
        if isinstance(content, str):
            self.content = {"text": content, "suggestions": []}
        else:
            self.content = {
                "text": content.get("text", ""),
                "suggestions": content.get("suggestions", [])
            }
        self.blocks = blocks or []
        self.children = children or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "title": self.title,
            "content": self.content,
            "blocks": [block.to_dict() for block in self.blocks],
            "children": [child.node_id for child in self.children]
        }

    @staticmethod
    def from_dict(data: Dict[str, Any], node_dir: str = None) -> 'ContentNode':
        blocks = [ContentBlock.from_dict(b) for b in data.get("blocks", [])]
        children = []
        if node_dir and "children" in data:
            for child_id in data["children"]:
                child_path = os.path.join(node_dir, f"{child_id}.json")
                if os.path.exists(child_path):
                    with open(child_path, "r", encoding="utf-8") as f:
                        child_data = json.load(f)
                    children.append(ContentNode.from_dict(child_data, node_dir))
        node = ContentNode(
            title=data["title"],
            content=data.get("content", {"text": "", "suggestions": []}),
            node_id=data["node_id"],
            children=children,
            blocks=blocks
        )
        return node

class Project:
    def __init__(self, name: str, base_path: str, root_node: Optional[ContentNode] = None):
        self.name = name
        self.base_path = base_path
        self.project_path = os.path.join(base_path, name)
        root_node_path = os.path.join(self.project_path, "root.json")
        if os.path.exists(root_node_path):
            with open(root_node_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.root_node = ContentNode.from_dict(data, self.project_path)
        elif root_node is not None:
            self.root_node = root_node
            self.save_node(self.root_node)
        else:
            self.root_node = ContentNode("Root node", {"text": "This is the root node.", "suggestions": []})
            self.save_node(self.root_node)

    def save_node(self, node: ContentNode):
        os.makedirs(self.project_path, exist_ok=True)
        filename = "root.json" if node == self.root_node else f"{node.node_id}.json"
        node_path = os.path.join(self.project_path, filename)
        with open(node_path, "w", encoding="utf-8") as f:
            json.dump(node.to_dict(), f, indent=2)
        for child in node.children:
            self.save_node(child)

    def load_node(self, node_id: str) -> ContentNode:
        filename = "root.json" if node_id == self.root_node.node_id else f"{node_id}.json"
        node_path = os.path.join(self.project_path, filename)
        with open(node_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return ContentNode.from_dict(data, self.project_path)

    def add_child_node(self, parent: ContentNode, child: ContentNode):
        parent.children.append(child)
        self.save_node(parent)
        self.save_node(child)

    def add_block(self, node: ContentNode, block: ContentBlock):
        node.blocks.append(block)
        self.save_node(node)

    def set_block_content(self, block: ContentBlock, new_content: Any, node: ContentNode):
        if isinstance(new_content, str):
            block.content["text"] = new_content
        elif isinstance(new_content, dict):
            block.content["text"] = new_content.get("text", block.content.get("text", ""))
            block.content["suggestions"] = new_content.get("suggestions", block.content.get("suggestions", []))
        self.save_node(node)

    def save_root(self):
        self.save_node(self.root_node)

    @staticmethod
    def load(name: str, base_path: str) -> 'Project':
        project_path = os.path.join(base_path, name)
        root_path = os.path.join(project_path, "root.json")
        if not os.path.exists(root_path):
            raise FileNotFoundError(f"No root node found for project '{name}'")
        with open(root_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        root_node = ContentNode.from_dict(data, project_path)
        return Project(name, base_path, root_node=root_node)

# --- LLM Helpers ---

llm = LLM()

def get_node_text(node: ContentNode, include_blocks: bool = True) -> str:
    texts = [node.content.get("text", "")]
    if include_blocks:
        for block in node.blocks:
            texts.append(block.content.get("text", ""))
    return "\n".join(texts)

def suggest(
    prompt: str,
    content: str,
    num_suggestions: int = 3
) -> list:
    example = '["First suggestion", "Second suggestion", "Third suggestion"]'
    full_prompt = (
        f"{prompt}\n\n"
        f"{content}\n"
        f"Return a JSON list of {num_suggestions} strings. For example: {example}"
    )
    messages = [HumanMessage(content=full_prompt)]
    response = llm.invoke(messages, stream=True, json=True)
    parsed = json.loads(response.content)
    if isinstance(parsed, dict) and len(parsed) == 1:
        value = next(iter(parsed.values()))
        if isinstance(value, list):
            return value
    if isinstance(parsed, list):
        return parsed
    raise ValueError("LLM did not return a JSON list of strings.")

class ConsoleContentManager:
    def __init__(self, base_path="./projects"):
        self.base_path = base_path
        self.project = None
        self.focus_node = None
        self.focus_block = None
        self.parent_stack = []

    def list_projects(self):
        print("Available projects:")
        for name in os.listdir(self.base_path):
            if os.path.isdir(os.path.join(self.base_path, name)):
                print(f" - {name}")

    def load_project(self, name):
        self.project = Project(name, self.base_path)
        self.focus_node = self.project.root_node
        self.focus_block = None
        self.parent_stack = []
        print(f"Loaded project: {name}")

    def create_project(self, name, root_title, root_content):
        self.project = Project(name, self.base_path, ContentNode(root_title, root_content))
        self.focus_node = self.project.root_node
        self.focus_block = None
        self.parent_stack = []
        print(f"Created new project: {name}")

    def show_node(self, node=None):
        if not self.project:
            print("No project loaded.")
            return
        node = node or self.focus_node or self.project.root_node
        self.focus_node = node
        print(f"\n# {node.title}")
        print("-" * 40)
        print("Text:", node.content.get("text", ""))
        if node.content.get("suggestions"):
            print("Suggestions:")
            for sset in node.content["suggestions"]:
                print(f"Prompt: {sset.get('prompt', '')}")
                for idx, s in enumerate(sset.get("results", []), 1):
                    print(f"  {idx}. {s}")
        if node.blocks:
            print("\n## Blocks:")
            for idx, block in enumerate(node.blocks, 1):
                print(f"  {idx}. **{block.title}**")
                print(f"      Text: {block.content.get('text', '')}")
                if block.content.get("suggestions"):
                    for sidx, suggestion in enumerate(block.content["suggestions"], 1):
                        print(f"      Suggestion {sidx}: {suggestion}")
        if node.children:
            print("\n## Nodes:")
            for idx, child in enumerate(node.children, 1):
                print(f"  {idx}. **{child.title}**")

    def add_block(self, node=None, title=None, content=None):
        node = node or self.focus_node
        if node is None:
            print("No node is focused.")
            return
        block = ContentBlock(title, content)
        self.project.add_block(node, block)
        self.focus_block = block
        print(f"Added block '{title}' and focused on it.")

    def add_node(self, parent_node=None, title=None, content=None):
        parent_node = parent_node or self.focus_node
        if parent_node is None:
            print("No node is focused.")
            return
        node = ContentNode(title, content)
        self.project.add_child_node(parent_node, node)
        self.focus_node = node
        self.focus_block = None
        print(f"Added node '{title}' and focused on it.")

    def edit_block(self, node=None, block_idx=None, new_content=None):
        node = node or self.focus_node
        if node is None:
            print("No node is focused.")
            return
        if self.focus_block is not None and block_idx is None:
            block = self.focus_block
        elif block_idx is not None:
            if 0 <= block_idx < len(node.blocks):
                block = node.blocks[block_idx]
            else:
                print("Invalid block index.")
                return
        else:
            print("No block is focused or index provided.")
            return
        self.project.set_block_content(block, new_content, node)
        print(f"Block '{block.title}' updated.")

    def edit_node(self, node=None, new_title=None, new_content=None):
        node = node or self.focus_node
        if node is None:
            print("No node is focused.")
            return
        node.title = new_title
        if isinstance(new_content, str):
            node.content["text"] = new_content
        elif isinstance(new_content, dict):
            node.content["text"] = new_content.get("text", node.content.get("text", ""))
            node.content["suggestions"] = new_content.get("suggestions", node.content.get("suggestions", []))
        self.project.save_node(node)
        print(f"Node '{new_title}' updated.")

    def delete_block(self, block_idx=None):
        node = self.focus_node
        if node is None:
            print("No node is focused.")
            return
        if not node.blocks:
            print("No blocks to delete.")
            return
        if block_idx is not None:
            if 0 <= block_idx < len(node.blocks):
                removed = node.blocks.pop(block_idx)
                if self.focus_block == removed:
                    if node.blocks:
                        new_idx = min(block_idx, len(node.blocks) - 1)
                        self.focus_block = node.blocks[new_idx]
                    else:
                        self.focus_block = None
                self.project.save_node(node)
                print(f"Deleted block '{removed.title}'.")
            else:
                print("Invalid block index.")
        elif self.focus_block is not None:
            try:
                idx = node.blocks.index(self.focus_block)
                removed = node.blocks.pop(idx)
                if node.blocks:
                    new_idx = min(idx, len(node.blocks) - 1)
                    self.focus_block = node.blocks[new_idx]
                else:
                    self.focus_block = None
                self.project.save_node(node)
                print(f"Deleted block '{removed.title}'.")
            except ValueError:
                print("Focused block not found in current node.")
        else:
            print("No block is focused or index provided.")

    def delete_node(self, node_idx=None):
        parent = self.parent_stack[-1] if self.parent_stack else None
        if node_idx is not None and self.focus_node:
            if not self.focus_node.children:
                print("No child nodes to delete.")
                return
            if 0 <= node_idx < len(self.focus_node.children):
                removed = self.focus_node.children.pop(node_idx)
                if self.focus_node == removed:
                    self.focus_node = parent
                    self.focus_block = None
                    if self.parent_stack:
                        self.parent_stack.pop()
                self.project.save_node(self.focus_node)
                print(f"Deleted child node '{removed.title}'.")
            else:
                print("Invalid node index.")
        elif parent and self.focus_node:
            try:
                idx = parent.children.index(self.focus_node)
                removed = parent.children.pop(idx)
                self.focus_node = parent
                self.focus_block = None
                self.parent_stack.pop()
                self.project.save_node(parent)
                print(f"Deleted node '{removed.title}' and moved focus to parent.")
            except ValueError:
                print("Focused node not found in parent.")
        else:
            print("No node is focused, or at root node.")
    
    def get_ancestor_context(self, node=None):
        """Return a string with the titles and main text of all ancestor nodes, from root to the given node (exclusive)."""
        if node is None:
            node = self.focus_node
        context_lines = []
        # parent_stack is from root to parent of current node
        for ancestor in self.parent_stack:
            context_lines.append(f"{ancestor.title}: {ancestor.content.get('text', '')}")
        return "\n".join(context_lines)
    
    def suggest_content(self):
        if not self.project:
            print("No project loaded.")
            return

        # Prefer focused block, else node
        if self.focus_block is not None:
            target = "block"
            content_text = self.focus_block.content.get("text", "")
            node = self.focus_node
        elif self.focus_node is not None:
            target = "node"
            content_text = self.focus_node.content.get("text", "")
            node = self.focus_node
        else:
            print("No node or block is focused.")
            return

        # Gather ancestor context
        ancestor_context = self.get_ancestor_context(node)
        if ancestor_context:
            context_for_llm = f"Context:\n{ancestor_context}\n\nContent:\n{content_text}"
        else:
            context_for_llm = content_text

        # Prompt selection (unchanged)
        print("\nChoose a prompt:")
        print("1. Expand/enhance this content (default)")
        print("2. Choose from pre-defined prompts")
        print("3. Enter a custom prompt")
        choice = input("Prompt option [1/2/3]: ").strip() or "1"

        if choice == "2":
            prompts = [
                "Suggest improvements to this content.",
                "Suggest next steps.",
                "Suggest related topics."
            ]
            for idx, p in enumerate(prompts, 1):
                print(f"{idx}. {p}")
            pidx = int(input("Select prompt number: ")) - 1
            prompt = prompts[pidx] if 0 <= pidx < len(prompts) else prompts[0]
        elif choice == "3":
            prompt = input("Enter your custom prompt: ")
        else:
            prompt = "Suggest ways to expand or enhance this content."

        # Call LLM with context
        try:
            suggestions = suggest(prompt, context_for_llm, num_suggestions=3)
        except Exception as e:
            print("LLM error:", e)
            return

        suggestion_obj = {"prompt": prompt, "results": suggestions}
        if target == "block":
            self.focus_block.content.setdefault("suggestions", []).append(suggestion_obj)
            self.project.save_node(self.focus_node)
            print("Suggestions added to block:")
            for idx, s in enumerate(suggestions, 1):
                print(f"  {idx}. {s}")
        else:
            self.focus_node.content.setdefault("suggestions", []).append(suggestion_obj)
            self.project.save_node(self.focus_node)
            print("Suggestions added to node:")
            for idx, s in enumerate(suggestions, 1):
                print(f"  {idx}. {s}")

    def use_suggestion(self):
        # Prefer focused block, else node
        if self.focus_block is not None:
            suggestions_list = self.focus_block.content.get("suggestions", [])
            content_obj = self.focus_block
            node = self.focus_node
        elif self.focus_node is not None:
            suggestions_list = self.focus_node.content.get("suggestions", [])
            content_obj = self.focus_node
            node = self.focus_node
        else:
            print("No node or block is focused.")
            return

        if not suggestions_list:
            print("No suggestions available.")
            return

        # Show all suggestion sets with their prompts
        print("\nAvailable suggestion sets:")
        for i, sset in enumerate(suggestions_list, 1):
            print(f"{i}. Prompt: {sset.get('prompt', '')}")
            for j, s in enumerate(sset.get("results", []), 1):
                print(f"   {j}. {s}")

        try:
            set_idx = int(input("Select suggestion set number: ")) - 1
            if not (0 <= set_idx < len(suggestions_list)):
                print("Invalid set selection.")
                return
            results = suggestions_list[set_idx]["results"]
            prompt = suggestions_list[set_idx]["prompt"]
        except Exception:
            print("Invalid input.")
            return

        for j, s in enumerate(results, 1):
            print(f"{j}. {s}")
        try:
            sidx = int(input("Select suggestion number to use: ")) - 1
            if not (0 <= sidx < len(results)):
                print("Invalid selection.")
                return
            suggestion = results[sidx]
        except Exception:
            print("Invalid input.")
            return

        print(f"\nPrompt used: {prompt}")
        print("\nWhat would you like to do with this suggestion?")
        print("1. Replace current content")
        print("2. Add as new block")
        print("3. Add as new child node")
        action = input("Choose [1/2/3]: ").strip() or "1"

        if action == "1":
            content_obj.content["text"] = suggestion
            self.project.save_node(node)
            print("Content replaced.")
        elif action == "2":
            title = input("Title for new block: ").strip() or "Suggestion"
            new_block = ContentBlock(title, suggestion)
            self.project.add_block(self.focus_node, new_block)
            print("Suggestion added as new block.")
        elif action == "3":
            title = input("Title for new node: ").strip() or "Suggestion"
            new_node = ContentNode(title, suggestion)
            self.project.add_child_node(self.focus_node, new_node)
            print("Suggestion added as new child node.")
        else:
            print("No action taken.")

    def interactive_loop(self):
        while True:
            cmd = input("\nCommand (help for options): ").strip().lower()
            if cmd == "help":
                print("Commands: list, load, create, show, addblock, addnode, editblock, editnode, focusnode, focusblock, up, quit")
            elif cmd == "list":
                self.list_projects()
            elif cmd == "load":
                name = input("Project name: ")
                self.load_project(name)
            elif cmd == "create":
                name = input("Project name: ")
                title = input("Root node title: ")
                content = input("Root node content: ")
                self.create_project(name, title, content)
            elif cmd == "show":
                self.show_node()
            elif cmd == "addblock":
                title = input("Block title: ")
                content = input("Block content: ")
                self.add_block(title=title, content=content)
            elif cmd == "addnode":
                title = input("Node title: ")
                content = input("Node content: ")
                self.add_node(title=title, content=content)
                self.show_node()
            elif cmd == "editblock":
                if self.focus_block is not None:
                    new_content = input(f"New content for block '{self.focus_block.title}': ")
                    self.edit_block(new_content=new_content)
                else:
                    idx = int(input("Block index (starting from 0): "))
                    new_content = input("New block content: ")
                    self.edit_block(block_idx=idx, new_content=new_content)
            elif cmd == "editnode":
                new_title = input("New node title: ")
                new_content = input("New node content: ")
                self.edit_node(new_title=new_title, new_content=new_content)
            elif cmd == "deleteblock":
                if self.focus_block is not None:
                    self.delete_block()
                else:
                    idx = int(input("Block index (starting from 0): "))
                    self.delete_block(block_idx=idx)
            elif cmd == "deletenode":
                if self.parent_stack and self.focus_node:
                    confirm = input(f"Delete focused node '{self.focus_node.title}'? (y/n): ").strip().lower()
                    if confirm == "y":
                        self.delete_node()
                else:
                    idx = int(input("Child node index (starting from 0): "))
                    self.delete_node(node_idx=idx)
            elif cmd == "focusnode":
                if not self.focus_node.children:
                    print("No child nodes to focus on.")
                else:
                    idx = int(input("Child node index (starting from 1): ")) - 1
                    if 0 <= idx < len(self.focus_node.children):
                        self.parent_stack.append(self.focus_node)
                        self.focus_node = self.focus_node.children[idx]
                        self.focus_block = None
                        print(f"Focused on node: {self.focus_node.title}")
                        self.show_node()
                    else:
                        print("Invalid index.")
            elif cmd == "focusblock":
                if not self.focus_node.blocks:
                    print("No blocks to focus on.")
                else:
                    idx = int(input("Block index (starting from 1): ")) - 1
                    if 0 <= idx < len(self.focus_node.blocks):
                        self.focus_block = self.focus_node.blocks[idx]
                        print(f"Focused on block: {self.focus_block.title}")
                    else:
                        print("Invalid index.")
            elif cmd == "up":
                if self.parent_stack:
                    self.focus_node = self.parent_stack.pop()
                    self.focus_block = None
                    print(f"Moved up to node: {self.focus_node.title}")
                    self.show_node()
                elif self.focus_node != self.project.root_node:
                    self.focus_node = self.project.root_node
                    self.focus_block = None
                    print(f"Moved up to root node: {self.focus_node.title}")
                    self.show_node()
                else:
                    print("Already at the root node.")
            elif cmd == "quit":
                print("Exiting.")
                break
            elif cmd == "showfocus":
                print(f"Focused node: {self.focus_node.title if self.focus_node else 'None'}")
                print(f"Focused block: {self.focus_block.title if self.focus_block else 'None'}")
            elif cmd == "suggest":
                self.suggest_content()
            elif cmd == "use":
                self.use_suggestion()
            else:
                print("Unknown command.")


if __name__ == "__main__":
    manager = ConsoleContentManager()
    manager.interactive_loop()