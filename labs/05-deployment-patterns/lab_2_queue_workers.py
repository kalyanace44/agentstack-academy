"""Lab 5.2: Queue-Based Agent Architecture

Decouple request intake from agent processing using a message queue.
Handles burst traffic, provides backpressure, and enables dead-letter queues.
"""
from __future__ import annotations

import time
import uuid
import threading
from collections import deque
from dataclasses import dataclass, field
from enum import Enum


class TaskStatus(Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    DEAD_LETTERED = "dead_lettered"


@dataclass
class Task:
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    payload: dict = field(default_factory=dict)
    status: TaskStatus = TaskStatus.QUEUED
    retries: int = 0
    max_retries: int = 3
    result: str = ""
    error: str = ""
    created_at: float = field(default_factory=time.time)
    completed_at: float = 0.0


class TaskQueue:
    """In-memory task queue with DLQ and backpressure."""

    def __init__(self, max_size: int = 100, max_retries: int = 3):
        self.queue: deque[Task] = deque()
        self.dlq: deque[Task] = deque()
        self.completed: list[Task] = []
        self.max_size = max_size
        self.max_retries = max_retries
        self._lock = threading.Lock()

    def enqueue(self, payload: dict) -> Task | None:
        """Add a task. Returns None if queue is full (backpressure)."""
        with self._lock:
            if len(self.queue) >= self.max_size:
                return None  # Backpressure signal
            task = Task(payload=payload, max_retries=self.max_retries)
            self.queue.append(task)
            return task

    def dequeue(self) -> Task | None:
        """Pull next task for processing."""
        with self._lock:
            if not self.queue:
                return None
            task = self.queue.popleft()
            task.status = TaskStatus.PROCESSING
            return task

    def complete(self, task: Task, result: str):
        task.status = TaskStatus.COMPLETED
        task.result = result
        task.completed_at = time.time()
        self.completed.append(task)

    def fail(self, task: Task, error: str):
        task.retries += 1
        task.error = error
        if task.retries >= task.max_retries:
            task.status = TaskStatus.DEAD_LETTERED
            self.dlq.append(task)
        else:
            task.status = TaskStatus.QUEUED
            with self._lock:
                self.queue.appendleft(task)  # Retry at front

    @property
    def stats(self) -> dict:
        return {
            "pending": len(self.queue),
            "completed": len(self.completed),
            "dead_lettered": len(self.dlq),
            "depth": len(self.queue),
        }


class AgentWorker:
    """Worker that pulls tasks and processes them."""

    def __init__(self, worker_id: str, queue: TaskQueue):
        self.id = worker_id
        self.queue = queue
        self.tasks_processed = 0

    def process_one(self) -> bool:
        """Process a single task. Returns False if queue is empty."""
        task = self.queue.dequeue()
        if not task:
            return False

        try:
            # Simulate agent processing (LLM call + tool use)
            query = task.payload.get("query", "")
            time.sleep(0.01)  # Simulate 10ms processing

            # Simulate occasional failures
            if "fail" in query.lower():
                raise RuntimeError("Simulated provider timeout")

            result = f"[Worker {self.id}] Processed: '{query[:50]}' → response generated"
            self.queue.complete(task, result)
            self.tasks_processed += 1
            return True
        except Exception as e:
            self.queue.fail(task, str(e))
            return True


# --- Demo ---

if __name__ == "__main__":
    print("=" * 70)
    print("  LAB 5.2: Queue-Based Agent Architecture")
    print("  Decouple intake from processing with backpressure + DLQ")
    print("=" * 70)
    print()

    queue = TaskQueue(max_size=10, max_retries=2)
    workers = [AgentWorker(f"w{i}", queue) for i in range(3)]

    # Simulate burst: 15 tasks arrive at once
    print("  📨 Simulating burst: 15 tasks arriving simultaneously...")
    accepted, rejected = 0, 0
    for i in range(15):
        query = f"Task {i}: analyze credit risk" if i % 5 != 0 else f"Task {i}: fail please"
        task = queue.enqueue({"query": query, "team": "lending"})
        if task:
            accepted += 1
        else:
            rejected += 1

    print(f"    Accepted: {accepted}, Rejected (backpressure): {rejected}")
    print(f"    Queue depth: {queue.stats['depth']}")
    print()

    # Workers process
    print("  ⚙️  Workers processing...")
    rounds = 0
    while queue.stats["pending"] > 0 and rounds < 20:
        for worker in workers:
            worker.process_one()
        rounds += 1

    print(f"    Rounds: {rounds}")
    for w in workers:
        print(f"    {w.id}: {w.tasks_processed} tasks processed")
    print()

    print(f"  📊 Final stats:")
    stats = queue.stats
    print(f"    Completed: {stats['completed']}")
    print(f"    Dead-lettered (failed {queue.max_retries}x): {stats['dead_lettered']}")
    print(f"    Pending: {stats['pending']}")

    if queue.dlq:
        print(f"\n  🪦 Dead Letter Queue:")
        for task in queue.dlq:
            print(f"    → {task.id}: '{task.payload['query'][:40]}' (retries: {task.retries}, error: {task.error})")

    print("\n  ✅ Queue architecture handles burst traffic + graceful failure recovery")
