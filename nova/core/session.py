from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
import uuid

from .events import Event


@dataclass
class Budgets:
    max_iters: int = 10
    max_calls: int = 50
    max_model_calls: int = 50


@dataclass
class Session:
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    state: dict[str, Any] = field(default_factory=dict)
    events: list[Event] = field(default_factory=list)
    budgets: Budgets = field(default_factory=Budgets)

    def emit(self, event: Event) -> None:
        self.events.append(event)

    def patch_state(self, patch: dict[str, Any]) -> None:
        # shallow merge for v1
        for k, v in patch.items():
            self.state[k] = v
        self.emit(Event(type="state_patched", data={"keys": list(patch.keys())}))
