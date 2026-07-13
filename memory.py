"""
memory.py — Conversation memory (keeps last N turns)
"""
from config import MEMORY_TURNS

class ConversationMemory:
    def __init__(self, k: int = MEMORY_TURNS):
        self.k = k
        self.turns = []

    def add(self, question: str, answer: str):
        self.turns.append((question, answer[:400]))
        if len(self.turns) > self.k:
            self.turns.pop(0)

    def get_history(self) -> str:
        if not self.turns:
            return "No previous conversation."
        lines = []
        for q, a in self.turns:
            lines.append(f"Human: {q}")
            lines.append(f"Assistant: {a}...")
        return "\n".join(lines)

    def clear(self):
        self.turns = []
