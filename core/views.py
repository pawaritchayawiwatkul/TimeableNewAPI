from fcm_django.models import FCMDevice
from rest_framework.viewsets import ViewSet
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import Response
from fcm_django.api.rest_framework import FCMDeviceAuthorizedViewSet

# Create your views here.

@permission_classes([IsAuthenticated])
class DeviceViewSet(FCMDeviceAuthorizedViewSet):
    def remove(self, request):
        try:
            device_id = request.data.get("device_id")
            if device_id == None:
                return Response({"error" : "Please Provide Device Id"}, status=400)
            device = FCMDevice.objects.get(user_id=request.user.id, registration_id=device_id)
            device.delete()
            return Response(status=200)
        except FCMDevice.DoesNotExist:
            return Response({"error" : "FCMDevice Not Found"}, status=404)
        