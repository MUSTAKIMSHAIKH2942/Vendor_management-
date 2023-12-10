from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import VendorViewSet, PurchaseOrderViewSet,RegisterAPI,LoginAPI

router = DefaultRouter()
router.register(r'vendors', VendorViewSet)
router.register(r'purchase_orders', PurchaseOrderViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('register/', RegisterAPI.as_view(), name='register'),
    path('login/', LoginAPI.as_view(), name='login'),
]
