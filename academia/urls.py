"""
URL configuration for academia project.
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Configuración de Swagger
schema_view = get_schema_view(
    openapi.Info(
        title="LinguaAcademy API",
        default_version='v1',
        description="API REST para el sistema de gestión de LinguaAcademy",
        contact=openapi.Contact(email="contacto@linguaacademy.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API REST
    path('api/v1/', include('core.api.urls')),
    
    # Documentación Swagger
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    # Tu página web principal
    path('', include('core.urls')),
]