# admin.py (FULL updated — no duplication, MovieRating integrated)

from django.contrib import admin
from django.contrib import admin
from .models import ETLRunLog
from .models import Movie, MovieLinks, Genre, MovieRating

from django.contrib import admin
from .models import MovieComment

@admin.register(MovieRating)
class MovieRatingAdmin(admin.ModelAdmin):
    list_display = ("movie", "user", "rating", "created_at", "updated_at")
    list_filter = ("rating", "created_at")
    search_fields = ("movie__title", "user__username", "user__email")
    autocomplete_fields = ("movie", "user")


class MovieLinksInline(admin.TabularInline):
    model = MovieLinks
    extra = 0


class MovieRatingInline(admin.TabularInline):
    model = MovieRating
    extra = 0
    autocomplete_fields = ("user",)
    fields = ("user", "rating", "created_at", "updated_at")
    readonly_fields = ("created_at", "updated_at")


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "language", "status", "rating", "rating_count", "duration", "slug", "created")
    list_filter = ("category", "language", "status", "created")
    search_fields = ("title", "cast")
    prepopulated_fields = {"slug": ("title",)}
    autocomplete_fields = ("genres",)

    inlines = [MovieLinksInline, MovieRatingInline]


@admin.register(MovieLinks)
class MovieLinksAdmin(admin.ModelAdmin):
    list_display = ("movie", "type", "link")
    search_fields = ("movie__title",)
    list_filter = ("type",)


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(MovieComment)
class MovieCommentAdmin(admin.ModelAdmin):
    list_display = ("movie", "user", "is_public", "created_at")
    list_filter = ("is_public", "created_at")
    search_fields = ("movie__title", "user__username", "user__email", "body")
    autocomplete_fields = ("movie", "user")

from django.contrib import admin
from .models import DailyMetric

@admin.register(DailyMetric)
class DailyMetricAdmin(admin.ModelAdmin):
    list_display = (
        "day",
        "views_total",
        "watches",
        "favorites",
        "sessions_search",
        "sessions_detail",
        "sessions_watch",
        "sessions_signup",
        "ratings_count_total",
        "avg_rating_global",
        "updated_at",
    )
    list_filter = ("day",)
    search_fields = ("day",)
    ordering = ("-day",)



@admin.register(ETLRunLog)
class ETLRunLogAdmin(admin.ModelAdmin):
    list_display = (
        "job_name",
        "status",
        "range_start",
        "range_end",
        "rows_updated",
        "duration_ms",
        "started_at",
        "finished_at",
    )
    list_filter = ("job_name", "status", "range_start")
    search_fields = ("job_name", "error_message")
    readonly_fields = ("created_at",)