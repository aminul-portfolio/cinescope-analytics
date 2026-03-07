# src/movie/tests/test_ratings.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from movie.models import Movie, MovieRating

User = get_user_model()


class MovieRatingTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="u1", password="pass12345")
        self.movie = Movie.objects.create(
            title="Test Movie",
            description="desc",
            image="movies/x.jpg",  # image field accepts string in tests if not validated by storage here
            category="action",
            language="english",
            status="RA",
            cast="a,b",
            year_of_production=timezone.now().date(),
            duration=100,
        )

    def test_create_rating_creates_single_row_and_updates_aggregates(self):
        self.client.login(username="u1", password="pass12345")

        url = reverse("movie:rate_movie", kwargs={"slug": self.movie.slug})
        resp = self.client.post(url, data={"rating": 8})
        self.assertEqual(resp.status_code, 302)

        self.assertEqual(MovieRating.objects.filter(user=self.user, movie=self.movie).count(), 1)

        self.movie.refresh_from_db()
        self.assertEqual(self.movie.rating_count, 1)
        self.assertEqual(self.movie.rating, 8.0)

    def test_update_rating_does_not_create_duplicate_row(self):
        self.client.login(username="u1", password="pass12345")

        url = reverse("movie:rate_movie", kwargs={"slug": self.movie.slug})
        self.client.post(url, data={"rating": 6})
        self.client.post(url, data={"rating": 9})

        self.assertEqual(MovieRating.objects.filter(user=self.user, movie=self.movie).count(), 1)

        mr = MovieRating.objects.get(user=self.user, movie=self.movie)
        self.assertEqual(mr.rating, 9)

        self.movie.refresh_from_db()
        self.assertEqual(self.movie.rating_count, 1)
        self.assertEqual(self.movie.rating, 9.0)

    def test_requires_login(self):
        url = reverse("movie:rate_movie", kwargs={"slug": self.movie.slug})
        resp = self.client.post(url, data={"rating": 7})
        # should redirect to login
        self.assertEqual(resp.status_code, 302)

    def test_invalid_rating_rejected(self):
        self.client.login(username="u1", password="pass12345")

        url = reverse("movie:rate_movie", kwargs={"slug": self.movie.slug})
        resp = self.client.post(url, data={"rating": 11})
        self.assertEqual(resp.status_code, 302)

        self.assertEqual(MovieRating.objects.filter(user=self.user, movie=self.movie).count(), 0)