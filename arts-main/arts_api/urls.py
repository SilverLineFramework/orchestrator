"""arts_api URL Configuration

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
from django.urls import path, re_path, include
from rest_framework_jwt.views import obtain_jwt_token
from rest_framework.schemas import get_schema_view
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static

from wasm_files import views as wf_views

urlpatterns = [
    path('admin/', admin.site.urls),
    re_path('arts-api/(?P<version>(v1|v2))/', include('arts_core.urls')),
    path('api-token-auth/', obtain_jwt_token, name='create-token'),
    path('wasm_files/', wf_views.UploadedFilesView.as_view(), name='wasm_files_list'),   
    path('wasm_files/u/', wf_views.wasm_file_upload, name='wasm_files_upload'),
    path('schema', get_schema_view(
        title="ARTS",
        description="API for ARTS",
        version="1.0.0"
    ), name='openapi-schema'), 
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
