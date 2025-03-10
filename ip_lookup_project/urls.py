"""
URL configuration for ip_lookup_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
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
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.conf import settings
from django.conf.urls.static import static
from ip_lookup_app import views




schema_view = get_schema_view(
    openapi.Info(
        title="IP Lookup API",
        default_version='v1',
        description="API for IP lookup",
    ),
    public=True,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    # path('api/', include('ip_lookup_app.urls')),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('', include('ip_lookup_app.urls')),

    path('api/aws/route53/records/', views.Route53RecordView.as_view(), name='dnsrecord-list'),
    path('api/aws/route53/records/<int:pk>/', views.Route53RecordDetailView.as_view(), name='dnsrecord-detail'),

    path('api/aws/route53/tasks/', views.Route53TaskListView.as_view(), name='task-list'),
    path('api/aws/route53/tasks/<str:task_id>/', views.Route53TaskDetailView.as_view(), name='task-detail'),
    path('api/aws/route53/tasks/<str:task_id>/apply/', views.apply_task_api, name='task-apply'),
    path('api/aws/route53/<int:record_id>/', views.get_route53_record, name='get_route53_record'),

]

# 仅在 DEBUG 模式下提供静态文件
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS)