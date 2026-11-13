import mimetypes
import os
import re

from django.conf import settings
from django.http import (FileResponse, Http404, HttpResponse,
                         HttpResponseNotModified)
from django.shortcuts import render
from django.templatetags.static import static
from django.utils._os import safe_join
from django.utils.http import http_date, parse_http_date_safe
from django.views.decorators.http import condition, require_GET, require_safe

from .models import Song


def _songs():
    return Song.objects.filter(is_active=True, page__lte=settings.BOOK_TOTAL_PAGES)


def _last_modified(request, *args, **kwargs):
    latest = _songs().order_by("-updated_at").values_list("updated_at", flat=True).first()
    return latest


@require_GET
@condition(last_modified_func=_last_modified)
def index(request):
    songs = {}
    for s in _songs():
        songs[s.page] = {
            "title": s.title,
            "src": s.src or "",
            "videoId": s.video_id,
            "start": s.start_time,
        }
    context = {
        "total_pages": settings.BOOK_TOTAL_PAGES,
        "pages": [{"n": n, "url": static(f"book/img/pages/{n}.jpg")} for n in range(1, settings.BOOK_TOTAL_PAGES + 1)],
        "songs": songs,
        "book_title": settings.BOOK_TITLE,
        "book_subtitle": settings.BOOK_SUBTITLE,
    }
    return render(request, "book/index.html", context)


@require_safe
def healthz(request):
    return HttpResponse("ok", content_type="text/plain")


_RANGE_RE = re.compile(r"bytes=(\d*)-(\d*)$")


@require_GET
def serve_media(request, path):
    """Serve uploaded media with HTTP Range support (required for audio seeking on iOS)."""
    try:
        full = safe_join(settings.MEDIA_ROOT, path)
    except Exception:
        raise Http404
    if not os.path.isfile(full):
        raise Http404

    stat = os.stat(full)
    size = stat.st_size
    mtime = int(stat.st_mtime)
    etag = f'"{mtime:x}-{size:x}"'
    ctype = mimetypes.guess_type(full)[0] or "application/octet-stream"

    inm = request.headers.get("If-None-Match")
    ims = parse_http_date_safe(request.headers.get("If-Modified-Since", ""))
    if (inm and etag in inm) or (not inm and ims is not None and mtime <= ims):
        resp = HttpResponseNotModified()
        resp["ETag"] = etag
        return resp

    start, end, status = 0, size - 1, 200
    m = _RANGE_RE.match(request.headers.get("Range", "").strip())
    if m and size:
        a, b = m.groups()
        if a == "" and b != "":          # suffix range: last N bytes
            start = max(size - int(b), 0)
        elif a != "":
            start = int(a)
            end = min(int(b), size - 1) if b != "" else size - 1
        if start > end or start >= size:
            resp = HttpResponse(status=416)
            resp["Content-Range"] = f"bytes */{size}"
            return resp
        status = 206

    length = end - start + 1
    f = open(full, "rb")
    f.seek(start)

    def chunks(fh, remaining, block=64 * 1024):
        try:
            while remaining > 0:
                data = fh.read(min(block, remaining))
                if not data:
                    break
                remaining -= len(data)
                yield data
        finally:
            fh.close()

    if request.method == "GET":
        resp = FileResponse(chunks(f, length), status=status, content_type=ctype)
    resp["Content-Length"] = str(length)
    resp["Accept-Ranges"] = "bytes"
    resp["ETag"] = etag
    resp["Last-Modified"] = http_date(mtime)
    resp["Cache-Control"] = "public, max-age=86400"
    if status == 206:
        resp["Content-Range"] = f"bytes {start}-{end}/{size}"
    return resp
