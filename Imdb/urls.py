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
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from movie.views import HomeView

urlpatterns = [
    path('', HomeView.as_view(), name='home'),  # 🎬 Homepage
    path('admin/', admin.site.urls),            # 🔐 Admin panel
    path('movies/', include('movie.urls', namespace='movie')),  # 🎞️ App URLs
]

# ✅ Static (dev) & Media (dev + Render coursework deploy)
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Portfolio/coursework Render deployment: serve /media/ from disk.
# Not a long-term production media strategy — use object storage/CDN in production.
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# 🚫 Custom 404 Error Page
handler404 = 'movie.views.custom_404_view'
