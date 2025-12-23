# nepse_scraper/urls.py
from django.utils import timezone
from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

# Health check endpoint
@csrf_exempt
def health_check(request):
    return JsonResponse({
        'status': 'healthy',
        'service': 'nepse-scraper',
        'timestamp': timezone.now().isoformat(),
        'endpoints': {
            'health': '/health/',
            'api_root': '/api/',
            'cron_test': '/api/cron/test/',
            'cron_simple': '/api/cron/simple/',
            'swagger': '/swagger/',
        }
    })

schema_view = get_schema_view(
    openapi.Info(
        title="NEPSE Scraper API",
        default_version='v1',
        description="Automated NEPSE stock data scraper.",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@nepse.local"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('scrapers.urls')),
    path('health/', health_check, name='health-check'),
    
    # Documentation
    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
