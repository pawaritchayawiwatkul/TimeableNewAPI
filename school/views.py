from django.shortcuts import render
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from school.serializers import CourseSerializer


# Create your views here.
@permission_classes([IsAuthenticated])
class CourseViewset(ViewSet):
    def create(self, request):
        data = dict(request.data)
        data["teacher_id"] = request.user.id
        ser = CourseSerializer(data=data)
        if ser.is_valid():
            obj = ser.create(validated_data=ser.validated_data)
            return Response(ser.data, status=200)
        else:
            return Response(ser.errors, status=400)
