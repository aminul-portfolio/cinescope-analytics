# src/movie/context_processors.py
from django.core.cache import cache
from .models import Genre

def genres_global(request):
    key = "navbar_genres_v1"
    genres = cache.get(key)
    if genres is None:
        genres = list(Genre.objects.only("id", "name").order_by("name"))
        cache.set(key, genres, 600)  # 10 minutes
    return {"genres": genres}