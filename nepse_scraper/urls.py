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
            name="NEPSE API",
            email="contact@nepse.local"
        ),
        license=openapi.License(
            name="MIT License",
        ),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

# Create a simple home view
def home_view(request):
    return JsonResponse({
        'message': 'NEPSE Stock Data API',
        'endpoints': {
            'stock_prices': '/api/stocks/latest/',
            'top_gainers': '/api/top-gainers/',
            'top_losers': '/api/top-losers/',
            'scrape_data': '/nepse/scrape/ (POST)',
            'documentation': '/swagger/',
        },
        'status': 'operational'
    })

urlpatterns = [
    path('admin/', admin.site.urls),
    path('nepse/', include('nepse_data.urls')),
    
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

# Serve static files during development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)