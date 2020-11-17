from django.conf.urls import url, include
from django.urls import path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework.routers import DefaultRouter

import core.views as core_views

schema_view = get_schema_view(
    openapi.Info(
        title="API",
        default_version='v1',
        description="Endpoints API docs",
    ),
    public=True,

)

router = DefaultRouter()
router.register(r'payments', core_views.PaymentsViewSet)
router.register(r'accounts', core_views.AccountsViewSet)

endpoints = [
                path('transfer/create/', core_views.CreateTransactionView.as_view())
            ] + router.urls

urlpatterns = [
    url(r'^api/v1/', include(endpoints)),
    url(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    url(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    url(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
