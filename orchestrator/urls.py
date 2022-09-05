"""Orchestrator APIs."""

from django.urls import path

from .views import list_modules, list_runtimes, search_runtime, search_module


urlpatterns = [
    path('runtimes/', list_runtimes),
    path('runtimes/<str:query>/', search_runtime),
    path('modules/', list_modules),
    path('modules/<str:query>/', search_module)
]
