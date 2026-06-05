from django.db import models
from django.utils.text import slugify


class InspirationCategory(models.Model):
    """A discipline or area of fitness that icons can be grouped under."""

    name = models.CharField(max_length=80)
    slug = models.SlugField(max_length=80, unique=True, blank=True)
    description = models.CharField(max_length=240)
    icon = models.CharField(max_length=8, default='💪', help_text='Single emoji')
    accent = models.CharField(
        max_length=20,
        default='emerald',
        help_text='CSS accent class (emerald/cyan/amber/violet/rose/sky)',
    )
    display_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['display_order', 'name']
        verbose_name_plural = 'Inspiration categories'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class FitnessIcon(models.Model):
    """A real-world fitness icon: bodybuilder, athlete, coach, etc."""

    slug = models.SlugField(max_length=120, unique=True, blank=True)
    name = models.CharField(max_length=120)
    nickname = models.CharField(max_length=120, blank=True)
    category = models.ForeignKey(
        InspirationCategory,
        on_delete=models.PROTECT,
        related_name='icons',
    )
    short_bio = models.CharField(max_length=240)
    bio = models.TextField(help_text='Markdown-free paragraph biography')
    image_url = models.URLField(blank=True)
    portrait_url = models.URLField(blank=True, help_text='Optional darker portrait crop')
    nationality = models.CharField(max_length=80, blank=True)
    born = models.CharField(max_length=80, blank=True)
    discipline = models.CharField(max_length=120, blank=True)
    achievements = models.TextField(
        blank=True,
        help_text='One achievement per line; renders as a bullet list',
    )
    training_tips = models.TextField(
        blank=True,
        help_text='Practical training/life tips from this icon',
    )
    signature_quote = models.CharField(max_length=400, blank=True)
    video_url = models.URLField(blank=True, help_text='YouTube embed URL')
    video_title = models.CharField(max_length=200, blank=True)
    instagram_url = models.URLField(blank=True)
    is_featured = models.BooleanField(default=False)
    display_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['display_order', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def achievement_list(self):
        return [a.strip() for a in self.achievements.splitlines() if a.strip()]

    @property
    def tip_list(self):
        return [t.strip() for t in self.training_tips.splitlines() if t.strip()]

    @property
    def youtube_id(self):
        from urllib.parse import urlparse, parse_qs
        if not self.video_url:
            return ''
        url = self.video_url
        if 'youtu.be' in url:
            return url.rsplit('/', 1)[-1].split('?')[0]
        if 'youtube.com' in url:
            qs = parse_qs(urlparse(url).query)
            return qs.get('v', [''])[0]
        return ''

    @property
    def youtube_embed_url(self):
        vid = self.youtube_id
        if not vid:
            return ''
        return f'https://www.youtube.com/embed/{vid}'


class MotivationQuote(models.Model):
    """A standalone motivational quote, optionally attributed to an icon."""

    text = models.TextField()
    author = models.CharField(max_length=120)
    icon = models.ForeignKey(
        FitnessIcon,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='quotes',
    )
    category = models.ForeignKey(
        InspirationCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='quotes',
    )
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_featured', '-created_at']

    def __str__(self):
        return f'"{self.text[:60]}..." — {self.author}'
