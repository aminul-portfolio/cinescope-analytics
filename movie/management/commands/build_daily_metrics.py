import datetime as dt
import time

from django.core.management.base import BaseCommand
from django.db.models import Avg, Sum
from django.utils import timezone

from movie.models import DailyMetric, ETLRunLog, Event, Favorite, Movie, MovieRating, WatchHistory


class Command(BaseCommand):
    help = "ETL: Build daily aggregate metrics (raw events -> daily metrics table)."

    def add_arguments(self, parser):
        parser.add_argument("--day", type=str, help="Process a single day YYYY-MM-DD")
        parser.add_argument("--from", dest="from_day", type=str, help="Start day YYYY-MM-DD (inclusive)")
        parser.add_argument("--to", dest="to_day", type=str, help="End day YYYY-MM-DD (inclusive)")
        parser.add_argument(
            "--backfill",
            action="store_true",
            help="Backfill from first event/watch/favorite/rating date to today",
        )

    def handle(self, *args, **options):
        tz = timezone.get_current_timezone()
        today = timezone.localdate()

        def parse_day(s: str) -> dt.date:
            return dt.datetime.strptime(s, "%Y-%m-%d").date()

        # -------------------------
        # Resolve date range
        # -------------------------
        if options.get("day"):
            start = end = parse_day(options["day"])
        elif options.get("backfill"):
            start = self._detect_first_date(today)
            end = today
        else:
            # Default: run yesterday (common daily ETL behavior)
            start = end = today - dt.timedelta(days=1)

        if options.get("from_day"):
            start = parse_day(options["from_day"])
        if options.get("to_day"):
            end = parse_day(options["to_day"])

        if start > end:
            self.stderr.write(self.style.ERROR("Invalid range: start > end"))
            return

        # -------------------------
        # ✅ ETL Run Log (enterprise observability)
        # -------------------------
        started_at = timezone.now()
        t0 = time.perf_counter()

        run_log = ETLRunLog.objects.create(
            job_name="build_daily_metrics",
            range_start=start,
            range_end=end,
            status=ETLRunLog.STATUS_SUCCESS,  # assume success unless exception
            rows_updated=0,
            started_at=started_at,
        )

        self.stdout.write(self.style.MIGRATE_HEADING(f"Building DailyMetrics: {start} → {end}"))

        rows_updated = 0
        try:
            cur = start
            while cur <= end:
                self._build_for_day(cur, tz)
                rows_updated += 1
                cur += dt.timedelta(days=1)

        except Exception as exc:
            run_log.status = ETLRunLog.STATUS_FAILED
            run_log.error_message = str(exc)[:5000]
            raise

        finally:
            finished_at = timezone.now()
            duration_ms = int((time.perf_counter() - t0) * 1000)

            run_log.rows_updated = rows_updated
            run_log.finished_at = finished_at
            run_log.duration_ms = max(duration_ms, 0)
            run_log.save(
                update_fields=["status", "error_message", "rows_updated", "finished_at", "duration_ms"]
            )

        self.stdout.write(self.style.SUCCESS("Done."))

    def _detect_first_date(self, fallback: dt.date) -> dt.date:
        """
        Find earliest date from any raw signal tables.
        """
        candidates = []

        e = Event.objects.order_by("created_at").values_list("created_at", flat=True).first()
        if e:
            candidates.append(timezone.localtime(e).date())

        w = WatchHistory.objects.order_by("watched_at").values_list("watched_at", flat=True).first()
        if w:
            candidates.append(timezone.localtime(w).date())

        f = Favorite.objects.order_by("created_at").values_list("created_at", flat=True).first()
        if f:
            candidates.append(timezone.localtime(f).date())

        r = MovieRating.objects.order_by("created_at").values_list("created_at", flat=True).first()
        if r:
            candidates.append(timezone.localtime(r).date())

        return min(candidates) if candidates else fallback

    def _build_for_day(self, day: dt.date, tz):
        start_dt = timezone.make_aware(dt.datetime.combine(day, dt.time.min), tz)
        end_dt = timezone.make_aware(dt.datetime.combine(day, dt.time.max), tz)

        # --- Raw counts ---
        watches = WatchHistory.objects.filter(watched_at__range=(start_dt, end_dt)).count()
        favorites = Favorite.objects.filter(created_at__range=(start_dt, end_dt)).count()

        # Event counts
        events = Event.objects.filter(created_at__range=(start_dt, end_dt))
        events_search = events.filter(event_type="search").count()
        events_detail_view = events.filter(event_type="detail_view").count()
        events_watch_click = events.filter(event_type="watch_click").count()
        events_signup_completed = events.filter(event_type="signup_completed").count()

        # Unique sessions per step
        sessions_search = (
            events.filter(event_type="search")
            .values("session_key")
            .exclude(session_key="")
            .distinct()
            .count()
        )
        sessions_detail = (
            events.filter(event_type="detail_view")
            .values("session_key")
            .exclude(session_key="")
            .distinct()
            .count()
        )
        sessions_watch = (
            events.filter(event_type="watch_click")
            .values("session_key")
            .exclude(session_key="")
            .distinct()
            .count()
        )
        sessions_signup = (
            events.filter(event_type="signup_completed")
            .values("session_key")
            .exclude(session_key="")
            .distinct()
            .count()
        )

        # Views snapshot (all-time sum)
        views_total = Movie.objects.aggregate(total=Sum("views_count"))["total"] or 0

        # Ratings snapshot (all-time)
        ratings_count_total = MovieRating.objects.count()
        avg_rating_global = MovieRating.objects.aggregate(avg=Avg("rating"))["avg"] or 0

        # Upsert into gold table
        obj, created = DailyMetric.objects.update_or_create(
            day=day,
            defaults={
                "views_total": views_total,
                "watches": watches,
                "favorites": favorites,
                "events_search": events_search,
                "events_detail_view": events_detail_view,
                "events_watch_click": events_watch_click,
                "events_signup_completed": events_signup_completed,
                "sessions_search": sessions_search,
                "sessions_detail": sessions_detail,
                "sessions_watch": sessions_watch,
                "sessions_signup": sessions_signup,
                "ratings_count_total": ratings_count_total,
                "avg_rating_global": round(float(avg_rating_global), 2),
            },
        )

        msg = (
            f"{day}  watches={watches} fav={favorites} "
            f"sessions_search={sessions_search} ratings={ratings_count_total}"
        )
        self.stdout.write(
            self.style.SUCCESS("UPDATED: " + msg) if not created else self.style.SUCCESS("CREATED: " + msg)
        )