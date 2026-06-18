from collections import deque


class ConversationManager:
    """Manages conversation history with dual interface:
    - add/get_messages: for LLM context (TokenManager style)
    - add_turn: for tracking entities/follow-ups (Alexa style)
    """

    def __init__(self, max_turns=5, max_tokens=6000):
        self.turns = deque(maxlen=max_turns)
        self.last_topic = None
        self.last_entity = None
        self.max_tokens = max_tokens
        self.history = []
        self.summary = ""

    def add(self, role, content):
        """Add a message to LLM history with token management."""
        self.history.append({"role": role, "content": content[:500]})
        total = sum(len(m["content"]) for m in self.history) // 4
        if total > self.max_tokens:
            self._compress()

    def _compress(self):
        if len(self.history) <= 6:
            return
        old = self.history[:-6]
        old_text = " | ".join(f"{m['role']}: {m['content'][:100]}" for m in old[-10:])
        self.summary = f"[Earlier: {old_text}]"
        self.history = self.history[-6:]

    def get_messages(self, system_prompt):
        """Get formatted messages for Groq API call."""
        messages = [{"role": "system", "content": system_prompt}]
        if self.summary:
            messages.append({"role": "system", "content": self.summary})
        messages.extend(self.history)
        return messages

    def add_turn(self, user_input, response, entities=None):
        """Track a conversation turn for context awareness."""
        self.turns.append({
            "user": user_input,
            "assistant": response,
            "entities": entities or []
        })
        if entities:
            self.last_entity = entities[-1]

    def get_context_string(self):
        """Format recent turns for display/debugging."""
        lines = []
        for turn in self.turns:
            lines.append(f"User: {turn['user']}")
            lines.append(f"Lester: {turn['assistant']}")
        return "\n".join(lines)

    def get_last_entity(self):
        return self.last_entity


# Singleton instance
convo = ConversationManager()
