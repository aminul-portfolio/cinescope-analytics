"""Imdb URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve as media_serve

from movie.views import HomeView

urlpatterns = [
    path('', HomeView.as_view(), name='home'),  # 🎬 Homepage
    path('admin/', admin.site.urls),            # 🔐 Admin panel
    path('movies/', include('movie.urls', namespace='movie')),  # 🎞️ App URLs
]

# ✅ Static files for local development only (WhiteNoise serves static on Render)
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Portfolio/coursework Render deployment: serve committed /media/ files from disk.
# django.conf.urls.static.static() adds no routes when DEBUG=False, so use serve() directly.
# Not a long-term production media strategy — use object storage/CDN in production.
urlpatterns += [
    re_path(
        r"^media/(?P<path>.*)$",
        media_serve,
        {"document_root": settings.MEDIA_ROOT},
    ),
]

# 🚫 Custom 404 Error Page
handler404 = 'movie.views.custom_404_view'
