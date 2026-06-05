from django.conf import settings
from django.db import models


class ChatSession(models.Model):
    """A single chat conversation. Anonymous users use session_key; logged-in users get a user FK."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='chat_sessions',
        null=True,
        blank=True,
    )
    session_key = models.CharField(max_length=64, blank=True, db_index=True)
    title = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        who = self.user.username if self.user else (self.session_key[:8] or 'anon')
        return f'Chat {who} @ {self.created_at:%Y-%m-%d %H:%M}'

    @property
    def message_count(self):
        return self.messages.count()


class ChatMessage(models.Model):
    """One turn in a chat conversation."""

    ROLE_USER = 'user'
    ROLE_BOT = 'bot'
    ROLE_SYSTEM = 'system'
    ROLE_CHOICES = [
        (ROLE_USER, 'User'),
        (ROLE_BOT, 'Bot'),
        (ROLE_SYSTEM, 'System'),
    ]

    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    intent = models.CharField(max_length=40, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at', 'id']

    def __str__(self):
        return f'[{self.role}] {self.content[:60]}'
