"""Attach local audio files to songs by page number.

Name files by page:  2.mp3, 3.mp3, ... 24.mp3  (m4a/ogg/wav also fine)

    python manage.py attach_audio /path/to/folder
"""
from pathlib import Path

from django.core.files import File
from django.core.management.base import BaseCommand, CommandError

from book.models import Song

EXTS = {".mp3", ".m4a", ".aac", ".ogg", ".opus", ".wav", ".webm"}


class Command(BaseCommand):
    help = "Attach audio files named <page>.<ext> from a folder to the matching Song."

    def add_arguments(self, parser):
        parser.add_argument("folder")

    def handle(self, *args, folder, **opts):
        base = Path(folder)
        if not base.is_dir():
            raise CommandError(f"{folder} is not a directory")
        done = 0
        for f in sorted(base.iterdir()):
            if f.suffix.lower() not in EXTS or not f.stem.isdigit():
                continue
            try:
                song = Song.objects.get(page=int(f.stem))
            except Song.DoesNotExist:
                self.stderr.write(f"skip {f.name}: no song on page {f.stem}")
                continue
            with f.open("rb") as fh:
                song.audio_file.save(f"{song.page}{f.suffix.lower()}", File(fh), save=True)
            self.stdout.write(self.style.SUCCESS(f"page {song.page}: {song.title} ← {f.name}"))
            done += 1
        self.stdout.write(f"{done} file(s) attached.")
