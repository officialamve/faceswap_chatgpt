import asyncio
from pathlib import Path
import pytest
from app.jobs import Job, JobManager

@pytest.mark.asyncio
async def test_enqueue_duplicate_and_finish():
    m = JobManager(); j = Job(1, Path('a'), Path('b')); m.enqueue(j)
    with pytest.raises(RuntimeError): m.enqueue(Job(1, Path('c'), Path('d')))
    assert await m.queue.get() is j
    m.finish(j); m.queue.task_done()
    m.enqueue(Job(1, Path('e'), Path('f')))

@pytest.mark.asyncio
async def test_queue_full_is_handled():
    m = JobManager(queue_size=1); m.enqueue(Job(1, Path('a'), Path('b')))
    with pytest.raises(RuntimeError): m.enqueue(Job(2, Path('c'), Path('d')))

def test_cancel_sets_flag():
    m = JobManager(); j = Job(1, Path('a'), Path('b')); m.enqueue(j)
    assert m.cancel(1) and j.cancelled
