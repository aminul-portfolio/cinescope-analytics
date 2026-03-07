# src/movie/urls.py (UPDATED — exports added, clean ordering)

from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views

from . import views
from .views import (
    MovieList,
    MovieDetail,
    MovieCategory,
    MovieLanguage,
    MovieSearch,
    MovieYear,
    AboutPage,
    signup_view,
    login_view,
    logout_view,
    dashboard_view,
)

app_name = "movie"

urlpatterns = [
    # Core pages
    path("", MovieList.as_view(), name="movie_list"),
    path("category/<str:category>/", MovieCategory.as_view(), name="movie_category"),
    path("language/<str:lang>/", MovieLanguage.as_view(), name="movie_language"),
    path("search/", MovieSearch.as_view(), name="movie_search"),
    path("about/", AboutPage.as_view(), name="about"),
    path("year/<int:year>/", MovieYear.as_view(), name="movie_year"),

    # Staff analytics
    path("analytics/", views.analytics_dashboard, name="analytics_dashboard"),

    # ✅ SaaS: CSV exports (keep near analytics)
    path("analytics/export/top-watches.csv", views.export_top_watches_csv, name="export_top_watches_csv"),
    path("analytics/export/top-favorites.csv", views.export_top_favorites_csv, name="export_top_favorites_csv"),
    path("analytics/export/top-rated.csv", views.export_top_rated_csv, name="export_top_rated_csv"),

    # Event tracking API (must be before slug catch-all)
    path("api/track-event/", views.track_event_api, name="track_event_api"),

    # ✅ Rating submit (MUST be before MovieDetail slug catch-all)
    path("<slug:slug>/rate/", views.rate_movie, name="rate_movie"),

    # ✅ Comments submit (MUST be before MovieDetail slug catch-all)
    path("<slug:slug>/comment/", views.add_comment, name="add_comment"),

    # Favorite/Watched
    path("movie/<slug:slug>/favorite/", views.toggle_favorite, name="toggle_favorite"),
    path("movie/<slug:slug>/watched/", views.mark_watched, name="mark_watched"),

    # Auth
    path("signup/", signup_view, name="signup"),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("dashboard/", dashboard_view, name="dashboard"),

    # Password Reset
    path(
        "password-reset/",
        auth_views.PasswordResetView.as_view(
            template_name="movie/password_reset_form.html",
            email_template_name="movie/password_reset_email.html",
            subject_template_name="movie/password_reset_subject.txt",
            success_url=reverse_lazy("movie:password_reset_done"),
        ),
        name="password_reset",
    ),
    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="movie/password_reset_done.html"
        ),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="movie/password_reset_confirm.html",
            success_url=reverse_lazy("movie:login"),
        ),
        name="password_reset_confirm",
    ),

    # Movie detail LAST (ONLY ONCE)
    path("<slug:slug>/", MovieDetail.as_view(), name="movie_detail"),
]