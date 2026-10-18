from enum import Enum
class FlowState(str, Enum):
    IDLE = "idle"
    SOURCE = "source"
    TARGET = "target"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETE = "complete"
    CANCELLED = "cancelled"
    FAILED = "failed"

class ConversationStore:
    def __init__(self): self._states = {}
    def get(self, user_id): return self._states.get(user_id, FlowState.IDLE)
    def set(self, user_id, state): self._states[user_id] = FlowState(state)
    def reset(self, user_id): self._states.pop(user_id, None)
