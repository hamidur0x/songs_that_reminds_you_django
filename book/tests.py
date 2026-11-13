import shutil
import tempfile

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Song

TMP = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=TMP)
class BookTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TMP, ignore_errors=True)

    def test_seed_and_index(self):
        self.assertEqual(Song.objects.count(), 23)
        r = self.client.get(reverse("index"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Tum Se Hi")
        self.assertContains(r, 'id="songs-data"')

    def test_conditional_get(self):
        r = self.client.get(reverse("index"))
        r2 = self.client.get(reverse("index"), HTTP_IF_MODIFIED_SINCE=r["Last-Modified"])
        self.assertEqual(r2.status_code, 304)

    def test_inactive_song_hidden(self):
        Song.objects.filter(page=2).update(is_active=False)
        self.assertNotContains(self.client.get(reverse("index")), "Tum Se Hi")

    def test_ad_free_flags(self):
        s = Song.objects.get(page=2)
        self.assertFalse(s.ad_free)
        s.audio_url = "https://example.com/a.mp3"
        self.assertTrue(s.ad_free)
        self.assertEqual(s.src, "https://example.com/a.mp3")

    def test_needs_a_source(self):
        with self.assertRaises(ValidationError):
            Song(page=99, title="x").full_clean()

    def test_media_range(self):
        s = Song.objects.get(page=2)
        s.audio_file.save("t.mp3", ContentFile(bytes(range(256)) * 4))
        url = s.audio_file.url
        full = self.client.get(url)
        self.assertEqual(full.status_code, 200)
        self.assertEqual(full["Accept-Ranges"], "bytes")
        part = self.client.get(url, HTTP_RANGE="bytes=10-19")
        self.assertEqual(part.status_code, 206)
        self.assertEqual(part["Content-Range"], "bytes 10-19/1024")
        self.assertEqual(b"".join(part.streaming_content), bytes(range(10, 20)))
        self.assertEqual(self.client.get(url, HTTP_RANGE="bytes=5000-").status_code, 416)
        self.assertEqual(self.client.get(url, HTTP_RANGE="bytes=-4").status_code, 206)
        self.assertEqual(self.client.get(url, HTTP_IF_NONE_MATCH=full["ETag"]).status_code, 304)

    def test_media_traversal(self):
        self.assertEqual(self.client.get("/media/../../etc/passwd").status_code, 404)

    def test_healthz(self):
        self.assertEqual(self.client.get(reverse("healthz")).content, b"ok")
