from django.urls import path
from .views import ListRuntimesView, RuntimeDetailView, ListModulesView, ModuleDetailView, LoginView, RegisterUsers, get_config

urlpatterns = [
    path('runtimes/', ListRuntimesView.as_view(), name="runtimes-all"),
    path('runtimes/<uuid:pk>/', RuntimeDetailView.as_view(), name="runtime-detail"),
    path('modules/', ListModulesView.as_view(), name="modules-all"),
    path('modules/<uuid:pk>/', ModuleDetailView.as_view(), name="module-detail"),
    path('auth/login/', LoginView.as_view(), name="auth-login"),
    path('auth/register/', RegisterUsers.as_view(), name="auth-register"),
    path('config/', get_config, name='get-config'),   
]