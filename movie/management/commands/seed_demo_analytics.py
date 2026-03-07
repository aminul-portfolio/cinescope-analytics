import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction

from movie.models import Movie, Favorite, WatchHistory


class Command(BaseCommand):
    help = "Seed demo analytics data: demo users, watch history, favorites, and boosted view counts."

    def add_arguments(self, parser):
        parser.add_argument('--users', type=int, default=100)
        parser.add_argument('--days', type=int, default=30)
        parser.add_argument('--seed', type=int, default=42)

    @transaction.atomic
    def handle(self, *args, **options):
        random.seed(options['seed'])

        users_n = options['users']
        days = options['days']
        User = get_user_model()

        movies = list(Movie.objects.all())
        if not movies:
            self.stdout.write(self.style.ERROR("No movies found. Add movies first (admin) then rerun seeder."))
            return

        # 1) Create demo users
        demo_users = []
        for i in range(1, users_n + 1):
            username = f"demo_user_{i:03d}"
            user, created = User.objects.get_or_create(username=username, defaults={
                "email": f"{username}@example.com"
            })
            if created:
                user.set_password("demo12345")
                user.save()
            demo_users.append(user)

        self.stdout.write(self.style.SUCCESS(f"Demo users ready: {len(demo_users)}"))

        # 2) Boost views_count with long-tail distribution
        #    A few movies become "hits"
        movies_sorted = sorted(movies, key=lambda m: (m.rating, m.created), reverse=True)
        for idx, m in enumerate(movies_sorted):
            # hit bias for top items
            base = max(5, int(400 / (idx + 1)))
            noise = random.randint(0, 120)
            m.views_count += base + noise
            m.save(update_fields=['views_count'])

        self.stdout.write(self.style.SUCCESS("Boosted Movie.views_count (long-tail)."))

        # 3) Generate watch history for last N days
        now = timezone.now()
        created_watches = 0
        created_favs = 0

        # Prefer higher rated + higher viewed movies
        weights = []
        for m in movies_sorted:
            w = (m.rating + 1.0) * (1 + (m.views_count / 500.0))
            weights.append(w)

        for u in demo_users:
            # assign each user a "session intensity"
            # light users watch 1–3; medium 4–10; heavy 10–25 (over 30 days)
            intensity = random.choices(
                population=['light', 'medium', 'heavy'],
                weights=[0.55, 0.35, 0.10],
                k=1
            )[0]

            if intensity == 'light':
                total_watches = random.randint(1, 3)
            elif intensity == 'medium':
                total_watches = random.randint(4, 10)
            else:
                total_watches = random.randint(10, 25)

            watched_movies = set()

            for _ in range(total_watches):
                m = random.choices(movies_sorted, weights=weights, k=1)[0]
                watched_movies.add(m.id)

                d = random.randint(0, days - 1)
                ts = now - timedelta(days=d, hours=random.randint(0, 23), minutes=random.randint(0, 59))

                WatchHistory.objects.create(
                    user=u,
                    movie=m,
                    watched_at=ts,
                    progress_seconds=random.randint(60, 60 * 60),
                    is_finished=random.random() < 0.35
                )
                created_watches += 1

            # Favorites: 10–25% of watched
            watched_movies = list(watched_movies)
            random.shuffle(watched_movies)
            fav_count = max(0, int(len(watched_movies) * random.uniform(0.10, 0.25)))

            for mid in watched_movies[:fav_count]:
                m = Movie.objects.get(id=mid)
                Favorite.objects.get_or_create(user=u, movie=m)
                created_favs += 1

        self.stdout.write(self.style.SUCCESS(
            f"Created watches: {created_watches}, favorites: {created_favs}"
        ))
        self.stdout.write(self.style.SUCCESS(
            "Done. Demo users password: demo12345"
        ))