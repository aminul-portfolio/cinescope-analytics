import csv
from datetime import timedelta

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.db.models import Count, Exists, OuterRef, Q, Sum
from django.db.models.functions import TruncDate
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, ListView, TemplateView

from .forms import MovieCommentForm, MovieRatingForm
from .models import (
    DailyMetric,
    ETLRunLog,
    Event,
    Favorite,
    Genre,
    Movie,
    MovieComment,
    MovieLinks,
    MovieRating,
    WatchHistory,
)
from .services import recalc_movie_rating

User = get_user_model()

# =========================================================
# Event Tracking
# =========================================================
def _get_session_key(request) -> str:
    """Ensure a session exists so we can track anonymous visitors consistently."""
    if not request.session.session_key:
        request.session.save()
    return request.session.session_key


def track_event(request, event_type, movie=None, link_type="", url="", meta=None):
    """
    Server-side event logger:
    - Anonymous via session_key
    - Members via user + session_key
    - Saves fields that exist on Event model (including meta JSONField)
    """
    session_key = _get_session_key(request)

    event_type = (event_type or "").strip()
    link_type = (link_type or "").strip()[:1]
    url = (url or "").strip()[:500]
    meta = meta or {}

    allowed = {"search", "detail_view", "watch_click", "signup_completed", "login", "download_click"}
    if event_type not in allowed:
        return

    Event.objects.create(
        event_type=event_type,
        session_key=session_key,
        user=request.user if request.user.is_authenticated else None,
        movie=movie,
        link_type=link_type,
        url=url,
        meta=meta,
    )


@csrf_exempt
@require_POST
def track_event_api(request):
    """
    Beacon endpoint for client-side tracking.
    Expects POST:
      - event_type
      - movie_id (optional)
      - link_type (optional)
      - url (optional)
    """
    session_key = _get_session_key(request)

    event_type = (request.POST.get("event_type") or "").strip()
    movie_id = (request.POST.get("movie_id") or "").strip()
    link_type = (request.POST.get("link_type") or "").strip()[:1]
    url = (request.POST.get("url") or "").strip()[:500]

    allowed = {"search", "detail_view", "watch_click", "signup_completed", "login", "download_click"}
    if event_type not in allowed:
        return JsonResponse({"ok": False, "error": "Invalid event_type"}, status=400)

    movie = None
    if movie_id.isdigit():
        movie = Movie.objects.filter(id=int(movie_id)).only("id").first()

    meta = {
        "path": request.path,
        "method": request.method,
        "ts": timezone.now().isoformat(),
        "ua": (request.META.get("HTTP_USER_AGENT") or "")[:300],
        "ref": (request.META.get("HTTP_REFERER") or "")[:300],
    }

    Event.objects.create(
        event_type=event_type,
        session_key=session_key,
        user=request.user if request.user.is_authenticated else None,
        movie=movie,
        link_type=link_type,
        url=url,
        meta=meta,
    )

    return JsonResponse({"ok": True})


# =========================================================
# Analytics Dashboard (staff-only)
# =========================================================
def _pct(part, whole):
    if not whole:
        return 0
    return round((part / whole) * 100, 1)


@staff_member_required
def analytics_dashboard(request):
    now = timezone.now()
    today = timezone.localdate()

    # ✅ SaaS: date range selector (7/30/90)
    try:
        days = int(request.GET.get("days", 30))
    except (TypeError, ValueError):
        days = 30
    if days not in (7, 30, 90):
        days = 30

    start_range = now - timedelta(days=days)
    start_7 = now - timedelta(days=7)

    # -------------------------
    # Core KPIs
    # -------------------------
    kpi_total_views = Movie.objects.aggregate(total=Sum("views_count"))["total"] or 0
    kpi_total_watches_range = WatchHistory.objects.filter(watched_at__gte=start_range).count()
    kpi_total_favorites_range = Favorite.objects.filter(created_at__gte=start_range).count()

    # ✅ Safer: ignore NULL users (if any)
    kpi_active_users_range = (
        WatchHistory.objects.filter(watched_at__gte=start_range, user__isnull=False)
        .values("user").distinct().count()
    )
    kpi_active_users_7d = (
        WatchHistory.objects.filter(watched_at__gte=start_7, user__isnull=False)
        .values("user").distinct().count()
    )

    # -------------------------
    # Trends (daily buckets, date range) - RAW tables
    # -------------------------
    days_list = [start_range.date() + timedelta(days=i) for i in range(days + 1)]
    labels = [d.strftime("%b %d") for d in days_list]

    watches_by_day = (
        WatchHistory.objects.filter(watched_at__gte=start_range)
        .annotate(day=TruncDate("watched_at"))
        .values("day")
        .annotate(c=Count("id"))
        .order_by("day")
    )
    favorites_by_day = (
        Favorite.objects.filter(created_at__gte=start_range)
        .annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(c=Count("id"))
        .order_by("day")
    )

    watches_by_day_map = {x["day"].strftime("%b %d"): x["c"] for x in watches_by_day if x["day"]}
    favorites_by_day_map = {x["day"].strftime("%b %d"): x["c"] for x in favorites_by_day if x["day"]}

    watches_series = [watches_by_day_map.get(lbl, 0) for lbl in labels]
    favorites_series = [favorites_by_day_map.get(lbl, 0) for lbl in labels]

    # -------------------------
    # ✅ ETL-backed series (DailyMetric = gold layer)
    # -------------------------
    dm_rows = (
        DailyMetric.objects.filter(day__gte=start_range.date(), day__lte=today)
        .values("day", "watches", "favorites")
        .order_by("day")
    )
    dm_map = {x["day"].strftime("%b %d"): x for x in dm_rows if x["day"]}
    dm_watches_series = [dm_map.get(lbl, {}).get("watches", 0) for lbl in labels]
    dm_favorites_series = [dm_map.get(lbl, {}).get("favorites", 0) for lbl in labels]

    # ✅ DE proof: Raw vs ETL parity check (range totals)
    etl_watches_sum = sum(dm_watches_series)
    etl_favorites_sum = sum(dm_favorites_series)

    etl_watches_delta = int(kpi_total_watches_range) - int(etl_watches_sum)
    etl_favorites_delta = int(kpi_total_favorites_range) - int(etl_favorites_sum)

    # -------------------------
    # Top tables (range-based)
    # -------------------------
    top_movies_watches = (
        Movie.objects.filter(watched_by__watched_at__gte=start_range)
        .annotate(watch_count=Count("watched_by", distinct=True))
        .order_by("-watch_count", "-rating", "-rating_count", "-views_count")[:10]
    )

    top_movies_favorites = (
        Movie.objects.filter(favorited_by__created_at__gte=start_range)
        .annotate(fav_count=Count("favorited_by", distinct=True))
        .order_by("-fav_count", "-rating", "-rating_count", "-views_count")[:10]
    )

    top_genres = (
        Genre.objects.filter(movie__watched_by__watched_at__gte=start_range)
        .annotate(watch_count=Count("movie__watched_by", distinct=True))
        .order_by("-watch_count", "name")[:10]
    )

    top_categories = (
        Movie.objects.filter(watched_by__watched_at__gte=start_range)
        .values("category")
        .annotate(watch_count=Count("watched_by", distinct=True))
        .order_by("-watch_count")
    )

    # Top rated (all-time)
    top_movies_rated = (
        Movie.objects.filter(rating_count__gt=0)
        .order_by("-rating", "-rating_count", "-views_count", "-created")[:10]
    )

    # -------------------------
    # Data Health panel
    # -------------------------
    movies_total = Movie.objects.count()
    missing_poster_count = Movie.objects.filter(Q(image__isnull=True) | Q(image="")).count()
    missing_trailer_count = Movie.objects.filter(Q(trailer_url__isnull=True) | Q(trailer_url="")).count()
    unrated_count = Movie.objects.filter(rating_count=0).count()

    watch_qs = MovieLinks.objects.filter(movie_id=OuterRef("pk"), type="W")
    movies_with_watch_count = (
        Movie.objects.annotate(has_watch=Exists(watch_qs)).filter(has_watch=True).count()
    )
    no_watch_count = max(movies_total - movies_with_watch_count, 0)
    watch_available_count = max(movies_total - no_watch_count, 0)

    # -------------------------
    # Journey funnel (SESSION-based, date range)
    # -------------------------
    base_events = (
        Event.objects.filter(created_at__gte=start_range)
        .exclude(session_key__isnull=True)
        .exclude(session_key="")
    )
    events_range_total = base_events.count()

    funnel_types = ["search", "detail_view", "watch_click", "signup_completed"]
    journey_events = base_events.filter(event_type__in=funnel_types)
    journey_events_range_total = journey_events.count()

    sessions_search = set(
        journey_events.filter(event_type="search").values_list("session_key", flat=True).distinct()
    )
    sessions_detail = set(
        journey_events.filter(event_type="detail_view").values_list("session_key", flat=True).distinct()
    )
    sessions_watch = set(
        journey_events.filter(event_type="watch_click").values_list("session_key", flat=True).distinct()
    )
    sessions_signup = set(
        journey_events.filter(event_type="signup_completed").values_list("session_key", flat=True).distinct()
    )

    step_search = sessions_search
    step_detail = step_search & sessions_detail
    step_watch = step_detail & sessions_watch

    sessions_base = len(step_search)
    search_sessions = len(step_search)
    detail_sessions = len(step_detail)
    watch_sessions = len(step_watch)

    signup_sessions = len(sessions_signup)
    signup_after_watch_sessions = len(sessions_watch & sessions_signup)

    range_label = f"{start_range.date()} → {today}"

    sessions_to_search_pct = 100.0 if sessions_base else 0
    search_to_detail_pct = _pct(detail_sessions, search_sessions)
    detail_to_watch_pct = _pct(watch_sessions, detail_sessions)
    watch_to_signup_pct = _pct(signup_after_watch_sessions, watch_sessions)

    search_rate_pct = 100.0 if sessions_base else 0
    detail_rate_pct = _pct(detail_sessions, sessions_base)
    watch_rate_pct = _pct(watch_sessions, sessions_base)
    signup_rate_pct = _pct(signup_sessions, sessions_base)

    # -------------------------
    # ✅ ETL Run Log + freshness (SaaS ops)
    # -------------------------
    etl_recent_runs = (
        ETLRunLog.objects
        .filter(job_name="build_daily_metrics")
        .order_by("-started_at")[:10]
    )
    latest = etl_recent_runs[0] if etl_recent_runs else None

    etl_is_stale = bool(
        latest and latest.finished_at and (timezone.now() - latest.finished_at).total_seconds() > 36 * 3600
    )

    # -------------------------
    # Context
    # -------------------------
    context = {
        "days": days,
        "range_label": range_label,

        # KPIs
        "kpi_total_views": kpi_total_views,
        "kpi_total_watches_range": kpi_total_watches_range,
        "kpi_total_favorites_range": kpi_total_favorites_range,
        "kpi_active_users_range": kpi_active_users_range,
        "kpi_active_users_7d": kpi_active_users_7d,

        # raw chart
        "labels": labels,
        "watches_series": watches_series,
        "favorites_series": favorites_series,

        # ETL-backed chart (DailyMetric)
        "dm_watches_series": dm_watches_series,
        "dm_favorites_series": dm_favorites_series,

        # ✅ DE parity proof
        "etl_watches_sum": etl_watches_sum,
        "etl_favorites_sum": etl_favorites_sum,
        "etl_watches_delta": etl_watches_delta,
        "etl_favorites_delta": etl_favorites_delta,

        # tables
        "top_movies_watches": top_movies_watches,
        "top_movies_favorites": top_movies_favorites,
        "top_movies_rated": top_movies_rated,
        "top_genres": top_genres,
        "top_categories": top_categories,

        # health
        "movies_total": movies_total,
        "missing_poster_count": missing_poster_count,
        "missing_trailer_count": missing_trailer_count,
        "no_watch_count": no_watch_count,
        "watch_available_count": watch_available_count,
        "unrated_count": unrated_count,

        # funnel counts
        "kpi_anon_sessions_range": sessions_base,
        "kpi_searches_range": search_sessions,
        "kpi_detail_views_range": detail_sessions,
        "kpi_watch_clicks_range": watch_sessions,
        "kpi_signups_range": signup_sessions,

        # funnel %
        "sessions_to_search_pct": sessions_to_search_pct,
        "search_to_detail_pct": search_to_detail_pct,
        "detail_to_watch_pct": detail_to_watch_pct,
        "watch_to_signup_pct": watch_to_signup_pct,

        # baseline %
        "search_rate_pct": search_rate_pct,
        "detail_rate_pct": detail_rate_pct,
        "watch_rate_pct": watch_rate_pct,
        "signup_rate_pct": signup_rate_pct,

        # debug
        "events_range_total": events_range_total,
        "journey_events_range_total": journey_events_range_total,

        # ETL log
        "etl_recent_runs": etl_recent_runs,
        "etl_last_run": latest,
        "etl_is_stale": etl_is_stale,
        "etl_job_name": "build_daily_metrics",
    }

    return render(request, "movie/analytics_dashboard.html", context)


# =========================================================
# Recommendations
# =========================================================
def get_recommendations_for_user(user, limit=12):
    """
    Personalized recommendations based on:
    - Favorites (strong signal)
    - Recent watch history (weak signal)
    Ranking: genre overlap -> rating -> views -> recency
    """
    if not user.is_authenticated:
        return Movie.objects.all().order_by("-views_count", "-rating", "-created")[:limit]

    liked_ids = Favorite.objects.filter(user=user).values_list("movie_id", flat=True)
    watched_ids = WatchHistory.objects.filter(user=user).values_list("movie_id", flat=True)

    seed_qs = Movie.objects.filter(id__in=liked_ids)
    if not seed_qs.exists():
        recent_ids = list(WatchHistory.objects.filter(user=user).values_list("movie_id", flat=True)[:10])
        seed_qs = Movie.objects.filter(id__in=recent_ids)

    if not seed_qs.exists():
        return Movie.objects.all().order_by("-views_count", "-rating", "-created")[:limit]

    preferred_genre_ids = (
        seed_qs.values_list("genres__id", flat=True).exclude(genres__id__isnull=True).distinct()
    )
    preferred_categories = seed_qs.values_list("category", flat=True).distinct()

    exclude_ids = set(liked_ids) | set(watched_ids)

    candidates = (
        Movie.objects.exclude(id__in=exclude_ids)
        .filter(Q(genres__id__in=preferred_genre_ids) | Q(category__in=preferred_categories))
        .annotate(
            genre_match=Count(
                "genres",
                filter=Q(genres__id__in=preferred_genre_ids),
                distinct=True,
            )
        )
        .distinct()
        .order_by("-genre_match", "-rating", "-views_count", "-created")
    )
    return candidates[:limit]


# =========================================================
# Static / Utility
# =========================================================
class AboutPage(TemplateView):
    template_name = "movie/about.html"


def custom_404_view(request, exception):
    return render(request, "movie/404.html", status=404)


# =========================================================
# Home (UPDATED: automatic sections)
# =========================================================
class HomeView(TemplateView):
    template_name = "movie/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        LIMIT = 20
        context["recently_added"] = Movie.objects.order_by("-created")[:LIMIT]
        context["top_rated"] = (
            Movie.objects.filter(rating_count__gt=0)
            .order_by("-rating", "-rating_count", "-created")[:LIMIT]
        )
        context["most_watched"] = Movie.objects.order_by("-views_count", "-created")[:LIMIT]
        context["slider_movies"] = (
            Movie.objects.exclude(banner="").exclude(banner__isnull=True).order_by("-created")[:5]
        )
        context["recommended_for_you"] = get_recommendations_for_user(self.request.user, limit=8)
        return context


# =========================================================
# Movie list (UPDATED: smart ordering + de-dup + overlap fix)
# =========================================================
class MovieList(ListView):
    model = Movie
    template_name = "movie/movie_list.html"
    paginate_by = 12

    def get_queryset(self):
        qs = super().get_queryset()

        query = (self.request.GET.get("query") or "").strip()
        category = self.request.GET.get("category")
        year = self.request.GET.get("year")
        genre = self.request.GET.get("genre")
        sort = self.request.GET.get("sort")
        status = self.request.GET.get("status")
        duration_max = self.request.GET.get("duration_max")
        watch_only = self.request.GET.get("watch_only")

        # Text search (title/cast/description + genre name)
        if query:
            qs = qs.filter(
                Q(title__icontains=query)
                | Q(cast__icontains=query)
                | Q(description__icontains=query)
                | Q(genres__name__icontains=query)
            ).distinct()

        # Year filter
        if year:
            try:
                year_int = int(year)
                qs = qs.filter(year_of_production__year=year_int)
            except ValueError:
                pass

        # Duration filter
        if duration_max:
            try:
                qs = qs.filter(duration__lte=int(duration_max))
            except ValueError:
                pass

        # Watch availability filter
        if watch_only == "1":
            qs = qs.filter(has_watch=True)

        # Status filter (optional, keep behavior)
        if status:
            qs = qs.filter(status=status)

        # De-dup + overlap fix: if both category & genre present, OR them
        if category and genre:
            qs = qs.filter(Q(category=category) | Q(genres__name__iexact=genre)).distinct()
        else:
            if category:
                qs = qs.filter(category=category)
            if genre:
                qs = qs.filter(genres__name__iexact=genre).distinct()

        SMART_ORDER = ["-rating", "-rating_count", "-views_count", "-created"]
        filters_active = any([query, category, genre, year, status, duration_max, watch_only])

        if sort == "views":
            qs = qs.order_by("-views_count", "-rating", "-rating_count", "-created")
        elif sort == "new":
            qs = qs.order_by("-created")
        elif sort == "rating":
            qs = qs.order_by(*SMART_ORDER)
        else:
            qs = qs.order_by(*SMART_ORDER) if filters_active else qs.order_by("-created")

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["selected_category"] = self.request.GET.get("category", "")
        context["selected_year"] = self.request.GET.get("year", "")
        context["selected_genre"] = self.request.GET.get("genre", "")
        context["selected_sort"] = self.request.GET.get("sort", "")
        context["selected_status"] = self.request.GET.get("status", "")
        context["selected_duration_max"] = self.request.GET.get("duration_max", "")
        context["selected_watch_only"] = self.request.GET.get("watch_only", "")

        context["genres"] = Genre.objects.all()
        context["years"] = Movie.objects.dates("year_of_production", "year", order="DESC")
        return context


# =========================================================
# Movie detail
# =========================================================
class MovieDetail(DetailView):
    model = Movie
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_object(self, queryset=None):
        obj = super().get_object(queryset=queryset)
        obj.views_count += 1
        obj.save()
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        movie = self.object

        track_event(self.request, "detail_view", movie=movie)

        context["links"] = MovieLinks.objects.filter(movie=movie)
        context["related_movies"] = Movie.objects.filter(category=movie.category).exclude(id=movie.id)[:6]
        context["recommended_for_you"] = get_recommendations_for_user(self.request.user, limit=9)
        context["comment_form"] = MovieCommentForm()
        context["comments"] = MovieComment.objects.filter(movie=movie, is_public=True).select_related("user")[:50]

        preferred_genre_ids = movie.genres.values_list("id", flat=True)
        context["because_this"] = (
            Movie.objects.exclude(id=movie.id)
            .filter(Q(genres__id__in=preferred_genre_ids) | Q(category=movie.category))
            .annotate(
                genre_match=Count(
                    "genres",
                    filter=Q(genres__id__in=preferred_genre_ids),
                    distinct=True,
                )
            )
            .distinct()
            .order_by("-genre_match", "-rating", "-views_count", "-created")
        )[:9]

        context["is_favorited"] = False
        if self.request.user.is_authenticated:
            context["is_favorited"] = Favorite.objects.filter(user=self.request.user, movie=movie).exists()

        # Rating form + user's existing rating
        context["rating_form"] = MovieRatingForm()
        context["my_rating"] = None
        if self.request.user.is_authenticated:
            existing = (
                MovieRating.objects.filter(user=self.request.user, movie=movie)
                .only("rating")
                .first()
            )
            context["my_rating"] = existing.rating if existing else None

        return context


# =========================================================
# Favorite + Watched
# =========================================================
@login_required
def toggle_favorite(request, slug):
    movie = get_object_or_404(Movie, slug=slug)
    fav, created = Favorite.objects.get_or_create(user=request.user, movie=movie)
    if not created:
        fav.delete()
    return redirect(reverse("movie:movie_detail", kwargs={"slug": slug}))


@login_required
def mark_watched(request, slug):
    movie = get_object_or_404(Movie, slug=slug)
    WatchHistory.objects.create(user=request.user, movie=movie)
    return redirect(reverse("movie:movie_detail", kwargs={"slug": slug}))


# =========================================================
# Category / Language
# =========================================================
class MovieCategory(ListView):
    model = Movie
    paginate_by = 5

    def get_queryset(self):
        self.category = self.kwargs["category"]
        return Movie.objects.filter(category=self.category)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["movie_category"] = self.category
        return context


class MovieLanguage(ListView):
    model = Movie
    paginate_by = 5

    def get_queryset(self):
        self.language = self.kwargs["lang"]
        return Movie.objects.filter(language=self.language)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["movie_language"] = self.language
        return context


# =========================================================
# Search (kept same behavior; only de-dup + top-rated-first improvements)
# =========================================================
class MovieSearch(ListView):
    model = Movie
    paginate_by = 9
    template_name = "movie/movie_search.html"

    def get_queryset(self):
        queryset = super().get_queryset()

        q = (self.request.GET.get("query") or "").strip()
        preset = (self.request.GET.get("preset") or "").strip().lower()

        category = (self.request.GET.get("category") or "").strip()
        year = (self.request.GET.get("year") or "").strip()
        genre = (self.request.GET.get("genre") or "").strip()
        sort = (self.request.GET.get("sort") or "").strip()
        status = (self.request.GET.get("status") or "").strip()
        duration_max = (self.request.GET.get("duration_max") or "").strip()
        watch_only = (self.request.GET.get("watch_only") or "").strip()

        watch_qs = MovieLinks.objects.filter(movie_id=OuterRef("pk"), type="W")
        queryset = queryset.annotate(has_watch=Exists(watch_qs))

        if watch_only == "1":
            queryset = queryset.filter(has_watch=True)

        if q:
            queryset = queryset.filter(
                Q(title__icontains=q)
                | Q(cast__icontains=q)
                | Q(description__icontains=q)
                | Q(genres__name__icontains=q)
            ).distinct()

        if not q and preset:
            if preset == "trending":
                queryset = queryset.filter(status="MW")
            elif preset == "top":
                queryset = queryset.filter(status="TR")
            elif preset == "new":
                queryset = queryset.filter(status="RA")
            elif preset == "best":
                queryset = queryset.all()
        elif not q and not preset:
            return Movie.objects.none()

        # ✅ overlap fix (category + genre)
        if category and genre:
            queryset = queryset.filter(Q(category=category) | Q(genres__name__iexact=genre)).distinct()
        else:
            if category:
                queryset = queryset.filter(category=category)

            if year:
                try:
                    year_int = int(year)
                    queryset = queryset.filter(year_of_production__year=year_int)
                except ValueError:
                    pass

            if genre:
                queryset = queryset.filter(genres__name__iexact=genre).distinct()

        if year:
            try:
                year_int = int(year)
                queryset = queryset.filter(year_of_production__year=year_int)
            except ValueError:
                pass

        if status:
            queryset = queryset.filter(status=status)

        if duration_max:
            try:
                dm = int(duration_max)
                queryset = queryset.filter(duration__lte=dm)
            except ValueError:
                pass

        SMART_ORDER = ["-rating", "-rating_count", "-views_count", "-created"]
        filters_active = any([q, preset, category, year, genre, status, duration_max, watch_only])

        if sort == "rating":
            queryset = queryset.order_by(*SMART_ORDER)
        elif sort == "views":
            queryset = queryset.order_by("-views_count", "-rating", "-rating_count", "-created")
        elif sort == "new":
            queryset = queryset.order_by("-created")
        else:
            queryset = queryset.order_by(*SMART_ORDER) if filters_active else queryset.order_by("-views_count", "-rating", "-created")

        page = (self.request.GET.get("page") or "").strip()
        if (q or preset) and (page in ("", "1")):
            track_event(
                self.request,
                "search",
                meta={
                    "query": q,
                    "preset": preset,
                    "category": category,
                    "year": year,
                    "genre": genre,
                    "duration_max": duration_max,
                    "watch_only": watch_only,
                    "sort": sort,
                    "status": status,
                    "path": self.request.path,
                    "ts": timezone.now().isoformat(),
                },
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["q"] = (self.request.GET.get("query") or "").strip()
        context["selected_preset"] = (self.request.GET.get("preset") or "").strip().lower()

        context["selected_category"] = (self.request.GET.get("category") or "").strip()
        context["selected_year"] = (self.request.GET.get("year") or "").strip()
        context["selected_genre"] = (self.request.GET.get("genre") or "").strip()
        context["selected_status"] = (self.request.GET.get("status") or "").strip()
        context["selected_sort"] = (self.request.GET.get("sort") or "").strip()
        context["selected_duration_max"] = (self.request.GET.get("duration_max") or "").strip()
        context["selected_watch_only"] = (self.request.GET.get("watch_only") or "").strip()

        full_qs = self.get_queryset()

        raw_cat_counts = full_qs.values("category").annotate(count=Count("id")).order_by("-count")
        cat_count_map = {x["category"]: x["count"] for x in raw_cat_counts}

        category_choices = [
            ("action", "Action"),
            ("drama", "Drama"),
            ("comedy", "Comedy"),
            ("romance", "Romance"),
        ]
        context["category_facets"] = [
            {"key": k, "label": label, "count": cat_count_map.get(k, 0)}
            for k, label in category_choices
            if cat_count_map.get(k, 0) > 0
        ]

        context["genre_facets"] = (
            Genre.objects.filter(movie__in=full_qs)
            .annotate(count=Count("movie"))
            .order_by("-count", "name")
        )

        context["year_facets"] = full_qs.dates("year_of_production", "year", order="DESC")
        return context


# =========================================================
# Year archive
# =========================================================
class MovieYear(ListView):
    model = Movie
    template_name = "movie/movie_list.html"
    paginate_by = 5

    def get_queryset(self):
        self.year = self.kwargs["year"]
        return Movie.objects.filter(year_of_production__year=self.year)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["selected_year"] = self.year
        context["genres"] = Genre.objects.all()
        context["years"] = Movie.objects.dates("year_of_production", "year", order="DESC")
        return context


# =========================================================
# Auth
# =========================================================
def signup_view(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            track_event(request, "signup_completed")
            return redirect("movie:dashboard")
    else:
        form = UserCreationForm()
    return render(request, "movie/signup.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            track_event(request, "login")
            return redirect("movie:dashboard")
    else:
        form = AuthenticationForm()
    return render(request, "movie/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("movie:login")


@login_required
def dashboard_view(request):
    return render(request, "movie/dashboard.html")


# =========================================================
# Rating submit
# =========================================================
@login_required
@require_POST
def rate_movie(request, slug):
    movie = get_object_or_404(Movie, slug=slug)

    form = MovieRatingForm(request.POST)
    if not form.is_valid():
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"ok": False, "errors": form.errors}, status=400)

        messages.error(request, "Please enter a valid rating (1–10).")
        return redirect(reverse("movie:movie_detail", kwargs={"slug": slug}))

    rating_value = form.cleaned_data["rating"]

    obj, created = MovieRating.objects.update_or_create(
        user=request.user,
        movie=movie,
        defaults={"rating": rating_value},
    )

    recalc_movie_rating(movie.id)

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        movie.refresh_from_db(fields=["rating", "rating_count"])
        return JsonResponse(
            {
                "ok": True,
                "created": created,
                "movie_id": movie.id,
                "avg_rating": movie.rating,
                "rating_count": movie.rating_count,
                "your_rating": obj.rating,
            }
        )

    messages.success(request, "Your rating has been saved.")
    return redirect(reverse("movie:movie_detail", kwargs={"slug": slug}))

@login_required
@require_POST
def add_comment(request, slug):
    movie = get_object_or_404(Movie, slug=slug)

    form = MovieCommentForm(request.POST)
    if not form.is_valid():
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"ok": False, "errors": form.errors}, status=400)

        messages.error(request, "Please write a valid comment.")
        return redirect(reverse("movie:movie_detail", kwargs={"slug": slug}))

    comment = MovieComment.objects.create(
        movie=movie,
        user=request.user,
        body=form.cleaned_data["body"],
        is_public=True,
    )

    # optional: track as an event (does not break existing tracking)
    # track_event(request, "comment_created", movie=movie)  # only if you add this type to allowed list

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({
            "ok": True,
            "id": comment.id,
            "body": comment.body,
            "created_at": comment.created_at.isoformat(),
            "user": getattr(request.user, "username", "You"),
        })

    messages.success(request, "Comment posted.")
    return redirect(reverse("movie:movie_detail", kwargs={"slug": slug}))
@staff_member_required
def export_top_watches_csv(request):
    now = timezone.now()
    try:
        days = int(request.GET.get("days", 30))
    except (TypeError, ValueError):
        days = 30
    if days not in (7, 30, 90):
        days = 30

    start_range = now - timedelta(days=days)

    rows = (
        Movie.objects.filter(watched_by__watched_at__gte=start_range)
        .annotate(watch_count=Count("watched_by", distinct=True))
        .order_by("-watch_count", "-rating", "-rating_count", "-views_count")[:100]
    )

    resp = HttpResponse(content_type="text/csv")
    resp["Content-Disposition"] = f'attachment; filename="top_watches_{days}d.csv"'
    w = csv.writer(resp)
    w.writerow(["title", "slug", "category", "year", "watch_count", "rating", "rating_count", "views_count"])

    for m in rows:
        w.writerow([
            m.title,
            m.slug,
            getattr(m, "category", ""),
            getattr(getattr(m, "year_of_production", None), "year", ""),
            getattr(m, "watch_count", 0),
            m.rating,
            getattr(m, "rating_count", 0),
            m.views_count,
        ])
    return resp


@staff_member_required
def export_top_favorites_csv(request):
    now = timezone.now()
    try:
        days = int(request.GET.get("days", 30))
    except (TypeError, ValueError):
        days = 30
    if days not in (7, 30, 90):
        days = 30

    start_range = now - timedelta(days=days)

    rows = (
        Movie.objects.filter(favorited_by__created_at__gte=start_range)
        .annotate(fav_count=Count("favorited_by", distinct=True))
        .order_by("-fav_count", "-rating", "-rating_count", "-views_count")[:100]
    )

    resp = HttpResponse(content_type="text/csv")
    resp["Content-Disposition"] = f'attachment; filename="top_favorites_{days}d.csv"'
    w = csv.writer(resp)
    w.writerow(["title", "slug", "category", "year", "fav_count", "rating", "rating_count", "views_count"])

    for m in rows:
        w.writerow([
            m.title,
            m.slug,
            getattr(m, "category", ""),
            getattr(getattr(m, "year_of_production", None), "year", ""),
            getattr(m, "fav_count", 0),
            m.rating,
            getattr(m, "rating_count", 0),
            m.views_count,
        ])
    return resp


@staff_member_required
def export_top_rated_csv(request):
    rows = (
        Movie.objects.filter(rating_count__gt=0)
        .order_by("-rating", "-rating_count", "-views_count", "-created")[:100]
    )

    resp = HttpResponse(content_type="text/csv")
    resp["Content-Disposition"] = 'attachment; filename="top_rated_all_time.csv"'
    w = csv.writer(resp)
    w.writerow(["title", "slug", "category", "year", "rating", "rating_count", "views_count"])

    for m in rows:
        w.writerow([
            m.title,
            m.slug,
            getattr(m, "category", ""),
            getattr(getattr(m, "year_of_production", None), "year", ""),
            m.rating,
            getattr(m, "rating_count", 0),
            m.views_count,
        ])
    return resp