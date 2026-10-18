import asyncio, time, uuid
from dataclasses import dataclass, field
from pathlib import Path

@dataclass
class Job:
    user_id: int
    source: Path
    target: Path
    created_at: float = field(default_factory=time.monotonic)
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    cancelled: bool = False
    task: asyncio.Task | None = None

class JobManager:
    def __init__(self, queue_size=1):
        self.queue = asyncio.Queue(maxsize=queue_size)
        self.active: dict[int, Job] = {}
        self.seen_updates: set[int] = set()
    def enqueue(self, job: Job):
        if job.user_id in self.active: raise RuntimeError("A job is already active for this user.")
        self.active[job.user_id] = job
        try: self.queue.put_nowait(job)
        except asyncio.QueueFull:
            self.active.pop(job.user_id, None)
            raise RuntimeError("The processing queue is full. Try again shortly.")
    def cancel(self, user_id):
        job = self.active.get(user_id)
        if not job: return False
        job.cancelled = True
        # Native inference runs in a worker thread and cannot be safely interrupted.
        # The worker checks this flag before sending any result.
        return True
    def finish(self, job): self.active.pop(job.user_id, None)
