# src/movie/tests/test_comments.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from movie.models import Movie, MovieComment

User = get_user_model()

class MovieCommentTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="u1", password="pass12345")
        self.movie = Movie.objects.create(
            title="Test Movie",
            description="desc",
            image="movies/x.jpg",
            category="action",
            language="english",
            status="RA",
            cast="a,b",
            year_of_production=timezone.now().date(),
            duration=100,
        )

    def test_requires_login(self):
        url = reverse("movie:add_comment", kwargs={"slug": self.movie.slug})
        resp = self.client.post(url, data={"body": "Hello"})
        self.assertEqual(resp.status_code, 302)

    def test_create_comment(self):
        self.client.login(username="u1", password="pass12345")
        url = reverse("movie:add_comment", kwargs={"slug": self.movie.slug})
        resp = self.client.post(url, data={"body": "Great movie!"})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(MovieComment.objects.filter(movie=self.movie, user=self.user).count(), 1)

    def test_invalid_comment_rejected(self):
        self.client.login(username="u1", password="pass12345")
        url = reverse("movie:add_comment", kwargs={"slug": self.movie.slug})
        resp = self.client.post(url, data={"body": ""})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(MovieComment.objects.count(), 0)