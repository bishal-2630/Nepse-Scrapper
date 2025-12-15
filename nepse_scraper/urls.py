from django.contrib import admin
from django.urls import path, include, re_path
from django.http import JsonResponse
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Create simplified schema view
schema_view = get_schema_view(
    openapi.Info(
        title="NEPSE Stock Data API",
        default_version='v1',
        description="""
        # NEPSE Stock Market Data API
        
        """,
        contact=openapi.Contact(
            name="NEPSE API Support",
            email="contact@nepse.local"
        ),
        license=openapi.License(
            name="MIT License",
        ),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
    patterns=[
        path('api/', include('nepse_data.urls')),
    ],
)

# Create a simple home view
def home_view(request):
    return JsonResponse({
        'message': 'NEPSE Stock Data API',
        'version': 'v1.0',
        'endpoints': {
            'latest_stocks': '/api/stocks/latest/',
            'top_gainers': '/api/top-gainers/',
            'top_losers': '/api/top-losers/',
            'scrape_fresh': '/api/scrape-fresh/ (POST)',
            'system_status': '/api/status/',
            'documentation': '/swagger/',
            'redoc': '/redoc/',
        },
        'scheduled_scraping': 'Mon-Fri at 4:15 PM Nepal Time',
        'status': 'operational'
    })

urlpatterns = [
    path('admin/', admin.site.urls),
    path('nepse/', include('nepse_data.urls')),  # Legacy endpoints
    path('api/', include('nepse_data.urls')),    # API endpoints
    
    # Swagger URLs
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', 
            schema_view.without_ui(cache_timeout=0), 
            name='schema-json'),
    path('swagger/', 
        schema_view.with_ui('swagger', cache_timeout=0), 
        name='schema-swagger-ui'),
    path('redoc/', 
        schema_view.with_ui('redoc', cache_timeout=0), 
        name='schema-redoc'),
    
    path('', home_view, name='home'),
]




if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)