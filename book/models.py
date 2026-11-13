from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator, MinValueValidator
from django.db import models


class Song(models.Model):
    """The song that plays when a given page of the book is open.

    Playback priority (see ``source``):
      1. ``audio_file`` – uploaded file, played by a plain HTML5 <audio> tag → no ads, ever.
      2. ``audio_url``  – direct link to an audio file (CDN etc.)             → no ads, ever.
      3. ``video_id``   – YouTube fallback                                    → YouTube may show ads.
    """

    page = models.PositiveIntegerField(unique=True, validators=[MinValueValidator(1)],
                                       help_text="Page number in the book (1 = cover).")
    title = models.CharField(max_length=120)
    audio_file = models.FileField(
        upload_to="songs/", blank=True,
        validators=[FileExtensionValidator(["mp3", "m4a", "aac", "ogg", "opus", "wav", "webm"])],
        help_text="Upload an mp3/m4a. Plays with no ads.",
    )
    audio_url = models.URLField(blank=True, help_text="Or a direct link to an audio file (no ads).")
    video_id = models.CharField("YouTube video ID", max_length=20, blank=True,
                                help_text="Fallback only – YouTube can show ads.")
    start_time = models.PositiveIntegerField(default=0, help_text="Start second.")
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["page"]

    def __str__(self):
        return f"p{self.page} – {self.title}"

    def clean(self):
        if not (self.audio_file or self.audio_url or self.video_id):
            raise ValidationError("Give an audio file, an audio URL or a YouTube video ID.")

    @property
    def source(self):
        if self.audio_file:
            return "file"
        if self.audio_url:
            return "url"
        return "youtube"

    @property
    def ad_free(self):
        return self.source != "youtube"

    @property
    def src(self):
        if self.audio_file:
            return self.audio_file.url
        return self.audio_url
