import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name="Song",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("page", models.PositiveIntegerField(help_text="Page number in the book (1 = cover).", unique=True, validators=[django.core.validators.MinValueValidator(1)])),
                ("title", models.CharField(max_length=120)),
                ("audio_file", models.FileField(blank=True, help_text="Upload an mp3/m4a. Plays with no ads.", upload_to="songs/", validators=[django.core.validators.FileExtensionValidator(["mp3", "m4a", "aac", "ogg", "opus", "wav", "webm"])])),
                ("audio_url", models.URLField(blank=True, help_text="Or a direct link to an audio file (no ads).")),
                ("video_id", models.CharField(blank=True, help_text="Fallback only – YouTube can show ads.", max_length=20, verbose_name="YouTube video ID")),
                ("start_time", models.PositiveIntegerField(default=0, help_text="Start second.")),
                ("is_active", models.BooleanField(default=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["page"]},
        ),
    ]
