from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('django-admin/', admin.site.urls),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('lot-owner/', include('lot_owner_panel.urls', namespace='lot_owner_panel')),
    path('admin-panel/', include('admin_panel.urls', namespace='admin_panel')),
    path('', include('parking.urls', namespace='parking')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
