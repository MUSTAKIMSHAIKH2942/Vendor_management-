from rest_framework import viewsets,generics,status,permissions
from rest_framework.response import Response
from rest_framework.authtoken.serializers import AuthTokenSerializer
from django.db.models import F,Avg
from datetime import datetime, timedelta
from .models import Vendor, PurchaseOrder
from .serializers import VendorSerializer, PurchaseOrderSerializer,RegisterSerializer
from rest_framework.decorators import action
from knox.views import LoginView as KnoxLoginView
from django.contrib.auth import login

class RegisterAPI(generics.GenericAPIView):
    serializer_class = RegisterSerializer
    def post (self, request, *args, **kwargs):

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({'message':'User registration done'})
    
class LoginAPI(KnoxLoginView):
    permission_classes = (permissions.AllowAny,)

    def post (self, request, format=None):
        serializer = AuthTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user =serializer.validated_data['user']
        login(request, user)
        return super(LoginAPI, self).post(request, format=None)
    
class VendorViewSet(viewsets.ModelViewSet):
    permission_classes = [ permissions.IsAuthenticated ]

    queryset = Vendor.objects.all()
    serializer_class = VendorSerializer

    # New endpoint for Vendor Performance Metrics
    @action(detail=True, methods=['get'], url_path='performance')
    def performance_metrics(self, request, pk=None):

        vendor = self.get_object()

        # Retrieve and calculate performance metrics
        completed_pos = PurchaseOrder.objects.filter(vendor=vendor, status='completed')
        
        # On-Time Delivery Rate
        on_time_delivery_rate = completed_pos.filter(delivery_date__lte=F('acknowledgment_date')).count() / completed_pos.count() * 100 if completed_pos.count() > 0 else 0
        
        # Quality Rating Average
        quality_rating_avg = completed_pos.filter(quality_rating__isnull=False).aggregate(Avg('quality_rating'))['quality_rating__avg'] if completed_pos.count() > 0 else 0

        # Average Response Time
        response_times = completed_pos.filter(acknowledgment_date__isnull=False).annotate(response_time=F('acknowledgment_date') - F('issue_date')).aggregate(Avg('response_time'))['response_time__avg'] if completed_pos.count() > 0 else timedelta(seconds=0)
        average_response_time = response_times.total_seconds() / 60 if response_times.total_seconds() > 0 else 0

        # Fulfilment Rate
        fulfillment_rate = completed_pos.exclude(issue_date__isnull=False).count() / completed_pos.count() * 100 if completed_pos.count() > 0 else 0

        return Response({
            'on_time_delivery_rate': on_time_delivery_rate,
            'quality_rating_avg': quality_rating_avg,
            'average_response_time': average_response_time,
            'fulfillment_rate': fulfillment_rate
        })

class PurchaseOrderViewSet(viewsets.ModelViewSet):
    permission_classes = [ permissions.IsAuthenticated ]
    queryset = PurchaseOrder.objects.all()
    serializer_class = PurchaseOrderSerializer

    def perform_create(self, serializer):
        serializer.save()

        # # Update metrics when a new purchase order is created
        # self.update_metrics(serializer.instance.vendor)

    def perform_update(self, serializer):
        # original_instance = self.get_object()
        serializer.save()

    def perform_destroy(self, instance):
        # Update metrics when a purchase order is deleted
        instance.delete()

    @action(detail=True, methods=['post'], url_path='acknowledge')
    def acknowledge_order(self, request, pk=None):
        purchase_order = self.get_object()

        # Update acknowledgment_date
        purchase_order.acknowledgment_date = datetime.now()
        purchase_order.save()

        return Response({'message': 'Purchase order acknowledged successfully.'}, status=status.HTTP_200_OK)

