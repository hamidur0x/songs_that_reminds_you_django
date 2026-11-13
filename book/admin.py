from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from .models import Song

admin.site.site_header = "Songbook admin"
admin.site.site_title = "Songbook"


@admin.register(Song)
class SongAdmin(admin.ModelAdmin):
    list_display = ("page", "title", "playback", "start_time", "is_active")
    list_display_links = ("page", "title")
    list_editable = ("start_time", "is_active")
    list_filter = ("is_active",)
    search_fields = ("title", "video_id")
    ordering = ("page",)

    @admin.display(description="Playback")
    def playback(self, obj):
        if obj.ad_free:
            return format_html('<b style="color:#1a7f37">✔ ad-free ({})</b>', obj.source)
        return mark_safe('<span style="color:#b35900">YouTube (may show ads)</span>')
