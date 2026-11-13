# 💖 For My Love – Cinematic Songbook (Django)

Same 3D page-flip book as the original, rebuilt as a Django project with an admin panel and an **ad-free audio player**.

## Run it

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export DJANGO_DEBUG=1                # local dev (use DJANGO_SECRET_KEY in production)
python manage.py migrate             # creates the DB and loads your 23 songs
python manage.py createsuperuser
python manage.py runserver
```
Open http://127.0.0.1:8000 · admin at `/admin/`.

## 🚫 No ads on phones

YouTube's embedded player always decides for itself whether to show ads, and they can't be blocked
from a web page. So the player works like this:

| Song has…            | Plays with…                     | Ads |
|----------------------|---------------------------------|-----|
| an **audio file**    | plain HTML5 `<audio>`           | **none** |
| an **audio URL**     | plain HTML5 `<audio>`           | **none** |
| only a YouTube ID    | YouTube player (fallback)       | possible |

To make the whole book ad-free, add an mp3/m4a for each song (files you own or are licensed to use):

* **Admin:** `/admin/` → Songs → open a song → upload *Audio file* (or paste an *Audio URL*).
  The list shows ✔ ad-free / YouTube per page.
* **Bulk:** name files by page number (`2.mp3` … `24.mp3`) and run
  `python manage.py attach_audio /path/to/folder`.

Phone extras: lock-screen / headphone play-pause-next controls (Media Session API), seeking works on
iOS (Range requests), smooth fade-in between songs, start-second per song.

## Optimisations

* Fonts, icons, PageFlip.js are **self-hosted** – no Tailwind CDN, Google Fonts or Font Awesome requests
* WhiteNoise + hashed, gzip-compressed, 1-year-cached static files; GZip for HTML
* Page images lazy-loaded (current page ±4); `Last-Modified`/304 on the main page
* Page-flip sound is synthesised in the browser (no external mp3)
* YouTube API is only loaded if a page actually needs the fallback (privacy-enhanced `youtube-nocookie` host)

## Deploy (Render)

`render.yaml` is included (Blueprint). Set `DJANGO_SECRET_KEY` (auto-generated). Uploaded audio needs a
persistent disk (`DJANGO_MEDIA_ROOT=/var/data/media`, `DJANGO_DB_PATH=/var/data/db.sqlite3`) or use *Audio URL*
pointing at your own storage/CDN. Other env vars: `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`,
`BOOK_TOTAL_PAGES`, `BOOK_TITLE`, `BOOK_SUBTITLE`.

## Layout

```
config/          settings, urls, wsgi
book/            Song model, admin, views (+Range media server), tests, attach_audio command
templates/book/  index.html
static/book/     css, js (book.js, page-flip), fonts, img/pages/1..25.jpg
extras/          original QR code, cassette image, bear keychain files
```
Tests: `python manage.py test`

Made with ❤️ by Hamidur Rahman
# songs_that_reminds_you_django
