from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.text import slugify


CATEGORY_CHOICES = (
    ("action", "Action"),
    ("drama", "Drama"),
    ("comedy", "Comedy"),
    ("romance", "Romance"),
)

LANGUAGE_CHOICES = (
    ("english", "English"),
    ("german", "German"),
)

STATUS_CHOICES = (
    ("RA", "Recently Added"),
    ("MW", "Most Watched"),
    ("TR", "Top Rated"),
)

LINK_CHOICES = (
    ("D", "Download Link"),
    ("W", "Watch Link"),
)


class Event(models.Model):
    EVENT_TYPES = (
        ("search", "Search"),
        ("detail_view", "Detail View"),
        ("watch_click", "Watch Click"),
        ("signup_completed", "Signup Completed"),
        ("login", "Login"),
    )

    event_type = models.CharField(max_length=32, choices=EVENT_TYPES)
    session_key = models.CharField(max_length=64, db_index=True, null=True, blank=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    movie = models.ForeignKey(
        "Movie",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    link_type = models.CharField(max_length=1, blank=True)  # 'W' or 'D'
    meta = models.JSONField(default=dict, blank=True)
    url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["created_at", "event_type"]),
            models.Index(fields=["created_at", "session_key"]),
        ]

    def __str__(self):
        return f"{self.event_type} @ {self.created_at:%Y-%m-%d %H:%M:%S}"


class Genre(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Movie(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField(max_length=1000)
    image = models.ImageField(upload_to="movies/")
    banner = models.ImageField(upload_to="movies_banner/", blank=True, null=True)

    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES)
    language = models.CharField(max_length=15, choices=LANGUAGE_CHOICES)
    status = models.CharField(max_length=2, choices=STATUS_CHOICES)

    cast = models.TextField()
    year_of_production = models.DateField()
    duration = models.PositiveIntegerField(help_text="Duration in minutes")

    rating = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(10.0)],
    )
    rating_count = models.PositiveIntegerField(default=0)

    trailer_url = models.URLField(blank=True, null=True)
    genres = models.ManyToManyField(Genre, blank=True)

    views_count = models.PositiveIntegerField(default=0)

    created = models.DateTimeField(default=timezone.now)
    slug = models.SlugField(unique=True, blank=True, null=True)

    class Meta:
        ordering = ["-created"]

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title) or "movie"
            slug = base_slug
            counter = 1

            while Movie.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                counter += 1
                slug = f"{base_slug}-{counter}"

            self.slug = slug

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class MovieRating(models.Model):
    """
    Per-user rating: one row per (user, movie), updatable.
    No text review.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="movie_ratings",
    )
    movie = models.ForeignKey(
        "Movie",
        on_delete=models.CASCADE,
        related_name="user_ratings",
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "movie"],
                name="uniq_user_movie_rating",
            )
        ]
        indexes = [
            models.Index(fields=["movie", "rating"]),
            models.Index(fields=["user", "movie"]),
        ]

    def __str__(self):
        return f"{self.user} rated {self.movie} = {self.rating}"


class MovieLinks(models.Model):
    movie = models.ForeignKey(
        Movie,
        related_name="movie_watch_links",
        on_delete=models.CASCADE,
    )
    type = models.CharField(max_length=1, choices=LINK_CHOICES)
    link = models.URLField()

    def __str__(self):
        return f"{self.get_type_display()} - {self.movie.title}"


class Favorite(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="favorites",
    )
    movie = models.ForeignKey(
        "Movie",
        on_delete=models.CASCADE,
        related_name="favorited_by",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "movie")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} ♥ {self.movie}"


class WatchHistory(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="watch_history",
    )
    movie = models.ForeignKey(
        "Movie",
        on_delete=models.CASCADE,
        related_name="watched_by",
    )
    watched_at = models.DateTimeField(auto_now_add=True)

    progress_seconds = models.PositiveIntegerField(default=0)
    is_finished = models.BooleanField(default=False)

    class Meta:
        ordering = ["-watched_at"]

    def __str__(self):
        return f"{self.user} watched {self.movie} @ {self.watched_at}"


class MovieComment(models.Model):
    movie = models.ForeignKey(
        "Movie",
        on_delete=models.CASCADE,
        related_name="comments",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="movie_comments",
    )

    body = models.TextField(max_length=1000)
    is_public = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["movie", "created_at"]),
            models.Index(fields=["user", "created_at"]),
        ]

    def __str__(self):
        return f"Comment by {self.user} on {self.movie}"


class DailyMetric(models.Model):
    """
    Daily aggregate snapshot for analytics.
    Gold layer: pre-aggregated metrics for fast dashboards and exports.
    """

    day = models.DateField(unique=True, db_index=True)

    views_total = models.PositiveIntegerField(default=0)
    watches = models.PositiveIntegerField(default=0)
    favorites = models.PositiveIntegerField(default=0)

    events_search = models.PositiveIntegerField(default=0)
    events_detail_view = models.PositiveIntegerField(default=0)
    events_watch_click = models.PositiveIntegerField(default=0)
    events_signup_completed = models.PositiveIntegerField(default=0)

    sessions_search = models.PositiveIntegerField(default=0)
    sessions_detail = models.PositiveIntegerField(default=0)
    sessions_watch = models.PositiveIntegerField(default=0)
    sessions_signup = models.PositiveIntegerField(default=0)

    ratings_count_total = models.PositiveIntegerField(default=0)
    avg_rating_global = models.DecimalField(max_digits=4, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-day",)

    def __str__(self):
        return f"DailyMetric({self.day})"


class ETLRunLog(models.Model):
    STATUS_SUCCESS = "SUCCESS"
    STATUS_FAILED = "FAILED"

    STATUS_CHOICES = [
        (STATUS_SUCCESS, "Success"),
        (STATUS_FAILED, "Failed"),
    ]

    job_name = models.CharField(
        max_length=120,
        default="build_daily_metrics",
        db_index=True,
    )

    range_start = models.DateField()
    range_end = models.DateField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_SUCCESS,
        db_index=True,
    )
    rows_updated = models.PositiveIntegerField(default=0)

    started_at = models.DateTimeField()
    finished_at = models.DateTimeField(null=True, blank=True)
    duration_ms = models.PositiveIntegerField(default=0)

    error_message = models.TextField(blank=True, default="")

    triggered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="etl_runs",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-started_at"]
        indexes = [
            models.Index(fields=["job_name", "started_at"]),
            models.Index(fields=["status", "started_at"]),
        ]

    def __str__(self):
        return f"{self.job_name} {self.range_start}→{self.range_end} ({self.status})"