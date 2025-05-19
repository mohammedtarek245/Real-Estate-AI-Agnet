# history.py

class ConversationHistory:
    """
    Maintains a list of past user and assistant messages to provide context.
    """

    def __init__(self):
        self.history = []

    def add_message(self, role: str, message: str):
        """
        Generic method to add a message from 'user' or 'assistant'.
        """
        self.history.append({"role": role, "content": message})

    def add_user_message(self, message: str):
        """Adds a message from the user."""
        self.add_message("user", message)

    def add_assistant_message(self, message: str):
        """Adds a message from the assistant."""
        self.add_message("assistant", message)

    def get_formatted_history(self, max_pairs: int = 5):
        """
        Returns the most recent `max_pairs` user-assistant message pairs,
        formatted for use in a chat model prompt.
        """
        formatted = []
        pairs = []
        current_pair = []

        for message in self.history:
            current_pair.append(message)
            if len(current_pair) == 2:
                pairs.append(current_pair)
                current_pair = []

        # Flatten the last N pairs
        recent = pairs[-max_pairs:]
        for pair in recent:
            formatted.extend(pair)

        return formatted

    def get_all(self):
        """
        Returns the full history (list of all message dicts).
        """
        return self.history

    def get_history(self):
        """
        Alias for get_all(). Ensures compatibility with existing code.
        """
        return self.history

    def reset(self):
        """Clears the conversation history."""
        self.history = []
