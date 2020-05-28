from django.urls import path
from .views import ListRuntimesView, RuntimeDetailView, ListModulesView, LoginView, RegisterUsers

urlpatterns = [
    path('runtimes/', ListRuntimesView.as_view(), name="runtimes-all"),
    path('runtimes/<uuid:pk>/', RuntimeDetailView.as_view(), name="runtime-detail"),
    path('modules/', ListModulesView.as_view(), name="modules-all"),
    path('auth/login/', LoginView.as_view(), name="auth-login"),
    path('auth/register/', RegisterUsers.as_view(), name="auth-register")    
]