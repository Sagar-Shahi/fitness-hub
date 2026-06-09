"""Models for the gamification system.

Player stats (XP, level, streak shields, title), the badge catalog, the
user's unlocked badges, the quest catalog, the user's quest instances, and
an audit log of every XP-gaining event.

The catalog tables (Badge, Quest) hold definitions seeded via a management
command; the user-specific tables (PlayerStats, UserBadge, UserQuest,
XPEvent) hold live state per user.
"""

from django.conf import settings
from django.db import models
from django.utils import timezone


# ---------------------------------------------------------------------------
# Level / title rules
# ---------------------------------------------------------------------------

def xp_for_level(level: int) -> int:
    """Total cumulative XP required to *reach* the start of a level.

    Uses a soft quadratic curve: Level 1 starts at 0, Level 2 at 100, then
    it grows. Feels rewarding in the early game and meaningful in the late
    game.
    """
    if level <= 1:
        return 0
    return 100 * (level - 1) ** 2


def level_for_xp(xp: int) -> int:
    """Inverse of xp_for_level. Returns the level for a given XP total."""
    if xp <= 0:
        return 1
    level = 1
    while xp_for_level(level + 1) <= xp:
        level += 1
        if level > 999:  # safety
            break
    return level


def title_for_level(level: int) -> str:
    """Return the display title for a given level."""
    table = [
        (1,  'Rookie'),
        (3,  'Apprentice'),
        (5,  'Initiate'),
        (8,  'Warrior'),
        (12, 'Athlete'),
        (16, 'Champion'),
        (20, 'Hero'),
        (25, 'Titan'),
        (30, 'Legend'),
        (40, 'Mythic'),
        (50, 'Immortal'),
        (60, 'Transcendent'),
    ]
    title = table[0][1]
    for threshold, t in table:
        if level >= threshold:
            title = t
        else:
            break
    return title


# ---------------------------------------------------------------------------
# Player profile
# ---------------------------------------------------------------------------

class PlayerStats(models.Model):
    """One row per user. Live XP, level, streak shields, and chosen title."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='player_stats',
    )
    xp = models.PositiveIntegerField(default=0)
    streak_shields = models.PositiveSmallIntegerField(default=0)
    coins = models.PositiveIntegerField(default=0)
    custom_title = models.CharField(max_length=40, blank=True)
    last_active = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Player Stats'
        verbose_name_plural = 'Player Stats'

    def __str__(self):
        return f"{self.user.username} — Lv.{self.level} ({self.xp} XP)"

    @property
    def level(self) -> int:
        return level_for_xp(self.xp)

    @property
    def title(self) -> str:
        return self.custom_title.strip() or title_for_level(self.level)

    @property
    def xp_into_level(self) -> int:
        """XP earned since reaching the current level."""
        return self.xp - xp_for_level(self.level)

    @property
    def xp_to_next_level(self) -> int:
        """XP needed to reach the next level."""
        return xp_for_level(self.level + 1) - xp_for_level(self.level)

    @property
    def level_progress_percent(self) -> int:
        if self.xp_to_next_level <= 0:
            return 100
        return int(self.xp_into_level * 100 / self.xp_to_next_level)

    def reset_for_testing(self):
        self.xp = 0
        self.streak_shields = 0
        self.coins = 0
        self.custom_title = ''
        self.save()


# ---------------------------------------------------------------------------
# Badge catalog + user unlocks
# ---------------------------------------------------------------------------

class Badge(models.Model):
    """Static catalog of every badge a user can earn."""
    TIER_CHOICES = [
        ('bronze', 'Bronze'),
        ('silver', 'Silver'),
        ('gold',   'Gold'),
        ('platinum', 'Platinum'),
        ('mythic', 'Mythic'),
    ]

    code = models.SlugField(max_length=60, unique=True)
    name = models.CharField(max_length=80)
    description = models.CharField(max_length=200)
    icon = models.CharField(max_length=8, default='🏅')
    tier = models.CharField(max_length=10, choices=TIER_CHOICES, default='bronze')
    xp_reward = models.PositiveSmallIntegerField(default=0)
    is_secret = models.BooleanField(default=False)

    class Meta:
        ordering = ['tier', 'name']

    def __str__(self):
        return f"{self.icon} {self.name}"


class UserBadge(models.Model):
    """A badge unlocked by a specific user."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='badges',
    )
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)
    unlocked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'badge')
        ordering = ['-unlocked_at']

    def __str__(self):
        return f"{self.user.username} — {self.badge.name}"


# ---------------------------------------------------------------------------
# Quest catalog + user quest instances
# ---------------------------------------------------------------------------

class Quest(models.Model):
    """A quest template. Daily/weekly challenges are spawned from these."""
    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('one_time', 'One-time'),
    ]

    code = models.SlugField(max_length=60, unique=True)
    name = models.CharField(max_length=80)
    description = models.CharField(max_length=200)
    icon = models.CharField(max_length=8, default='🎯')
    frequency = models.CharField(max_length=10, choices=FREQUENCY_CHOICES, default='daily')
    target_type = models.CharField(max_length=40)  # 'workouts_logged', 'meals_logged', etc.
    target_count = models.PositiveSmallIntegerField(default=1)
    xp_reward = models.PositiveSmallIntegerField(default=25)
    coin_reward = models.PositiveSmallIntegerField(default=0)
    weight = models.PositiveSmallIntegerField(default=10)  # for daily rotation

    class Meta:
        ordering = ['frequency', '-weight', 'name']

    def __str__(self):
        return f"{self.icon} {self.name}"


class UserQuest(models.Model):
    """A live quest instance assigned to a user."""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('claimed', 'Claimed'),
        ('expired', 'Expired'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='user_quests',
    )
    quest = models.ForeignKey(Quest, on_delete=models.CASCADE)
    progress = models.PositiveSmallIntegerField(default=0)
    target = models.PositiveSmallIntegerField(default=1)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    assigned_date = models.DateField(default=timezone.localdate)
    expires_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    claimed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-assigned_date', 'id']
        indexes = [
            models.Index(fields=['user', 'status']),
        ]

    def __str__(self):
        return f"{self.user.username} — {self.quest.name} ({self.progress}/{self.target})"

    @property
    def percent(self) -> int:
        if self.target <= 0:
            return 100
        return min(100, int(self.progress * 100 / self.target))

    @property
    def is_complete(self) -> bool:
        return self.progress >= self.target

    @property
    def is_expired(self) -> bool:
        return self.expires_at is not None and self.expires_at < timezone.now()


# ---------------------------------------------------------------------------
# Audit log
# ---------------------------------------------------------------------------

class XPEvent(models.Model):
    """One row per XP-gaining event. Used for the activity feed and audit."""
    SOURCE_CHOICES = [
        ('workout', 'Workout logged'),
        ('goal', 'Goal created'),
        ('meal', 'Meal logged'),
        ('order', 'Order placed'),
        ('streak', 'Streak bonus'),
        ('badge', 'Badge unlocked'),
        ('quest', 'Quest completed'),
        ('level', 'Level bonus'),
        ('other', 'Other'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='xp_events',
    )
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES)
    amount = models.IntegerField()  # can be negative for corrections
    description = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
        ]

    def __str__(self):
        sign = '+' if self.amount >= 0 else ''
        return f"{self.user.username} {sign}{self.amount} XP — {self.source}"


class StreakShieldUse(models.Model):
    """Audit log for when a user burns a streak shield."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='shield_uses',
    )
    used_on = models.DateField(default=timezone.localdate)
    reason = models.CharField(max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-used_on']
        indexes = [
            models.Index(fields=['user', '-used_on']),
        ]

    def __str__(self):
        return f"{self.user.username} used shield on {self.used_on}"
