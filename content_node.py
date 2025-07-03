from typing import List, Dict, Optional
import uuid

class ContentNode:
    def __init__(
        self,
        goal: str,
        choices: List[str],
        is_dynamic: bool = False,
        content: Optional[str] = None,
        plot_summary: Optional[str] = None,
        player_state_snapshot: Optional[Dict] = None,
        node_id: Optional[str] = None
    ):
        self.id = node_id or str(uuid.uuid4())
        self.goal = goal
        self.choices = choices
        self.is_dynamic = is_dynamic
        self.content = content
        self.plot_summary = plot_summary or ""
        self.player_state_snapshot = player_state_snapshot or {}
        self.generated = bool(content)  # Has this node been generated yet?