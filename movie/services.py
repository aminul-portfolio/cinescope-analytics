# src/movie/services.py
from django.db.models import Avg, Count
from django.db import transaction

from .models import Movie, MovieRating


@transaction.atomic
def recalc_movie_rating(movie_id: int) -> None:
    """
    Recalculate aggregate rating fields on Movie from MovieRating rows.
    Updates:
      - Movie.rating (avg, float)
      - Movie.rating_count (int)
    """
    agg = (
        MovieRating.objects
        .filter(movie_id=movie_id)
        .aggregate(avg=Avg("rating"), cnt=Count("id"))
    )

    avg = agg["avg"] or 0.0
    cnt = agg["cnt"] or 0

    # store with 1 decimal for stable display/order
    avg = round(float(avg), 1)

    Movie.objects.filter(id=movie_id).update(rating=avg, rating_count=cnt)