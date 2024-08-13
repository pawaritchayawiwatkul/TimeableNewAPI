from rest_framework.views import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.decorators import api_view
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from student.models import CourseRegistration, Student, Course, Lesson, StudentTeacherRelation
from teacher.models import UnavailableTimeOneTime, UnavailableTimeRegular, Teacher
from django.utils import timezone
from datetime import timedelta, datetime
from django.db.models import Count, F, Func, Value, CharField, Prefetch
from datetime import datetime
from django.db.models.functions import ExtractWeek, Extract, ExtractMonth
from django.core.exceptions import ValidationError
from student.serializers import UnavailableTimeSerializer, ListLessonSerializer, CourseRegistrationSerializer, LessonSerializer, ListTeacherSerializer, ListCourseRegistrationSerializer, ListLessonDateTimeSerializer, ProfileSerializer
from django.shortcuts import get_object_or_404
from dateutil.relativedelta import relativedelta
from collections import defaultdict
from fcm_django.models import FCMDevice
from firebase_admin.messaging import Message, Notification

@permission_classes([IsAuthenticated])
class ProfileViewSet(ViewSet):
    def retrieve(self, request):
        try:
            user = request.user
            ser = ProfileSerializer(instance=user)
            return Response(ser.data)
        except Student.DoesNotExist:
            return Response(status=404)
    
    def update(self, request):
        user = request.user
        ser = ProfileSerializer(data=request.data)
        if ser.is_valid():
            user = ser.update(user, ser.validated_data)
            return Response(status=200)
        else:
            return Response(ser.errors, status=400)
        
    def add(self, request, teacher_uuid):
        user = request.user
        teacher = get_object_or_404(Teacher, user__uuid=teacher_uuid)
        student = get_object_or_404(Student, user_id=user.id)
        if not student.teacher.filter(id=teacher.id).exists():
            student.teacher.add(teacher)
            student.school.add(teacher.school_id)        
        return Response(status=200)
    
@permission_classes([IsAuthenticated])
class TeacherViewset(ViewSet):
    def list(self, request):
        user = request.user
        teacher = StudentTeacherRelation.objects.select_related("teacher__school", "teacher__user").order_by("favorite_teacher").filter(student__user_id=user.id)
        ser = ListTeacherSerializer(instance=teacher, many=True)
        return Response(ser.data)
    
    def favorite(self, request, code):
        fav = request.GET.get("fav", None)
        if fav in ["0", "1"]:
            fav = bool(int(fav))
            student = get_object_or_404(StudentTeacherRelation, teacher__user__uuid=code, student__user_id=request.user.id)
            student.favorite_teacher = bool(int(fav))
            student.save()
            return Response({"favorite": fav}, status=200)
        else:
            return Response({"error_messages": ["Invalid Request"]}, status=400)
    
@permission_classes([IsAuthenticated])
class CourseViewset(ViewSet):
    def favorite(self, request, code):
        fav = request.GET.get("fav", None)
        if fav in ["0", "1"]:
            fav = bool(int(fav))
            regis = CourseRegistration.objects.get(uuid=code, student__user_id=request.user.id)
            regis.student_favorite = bool(int(fav))
            regis.save()
            return Response({"favorite": fav}, status=200)
        else:
            return Response({"error_messages": ["Invalid Request"]}, status=400)
    
    def list(self, request):
        teacher_uuid = request.GET.get("teacher_uuid")
        if not teacher_uuid:
            return Response({"error_messages": ["Please Techer ID"]}, status=400)
        filters = {
            'student__user_id': request.user.id,
        }

        if teacher_uuid:
            # Assuming you have a Teacher model with a UUID field
            teacher = get_object_or_404(Teacher, user__uuid=teacher_uuid)
            filters['teacher'] = teacher

        courses = CourseRegistration.objects.select_related("course").filter(**filters)
        ser = ListCourseRegistrationSerializer(instance=courses, many=True)
        return Response(ser.data)

    def get_available_time(self, request, code):
        date_str = request.GET.get("date", None)
        if not date_str:
            return Response({"error_messages": ["Please Provide Date"]}, status=400)
        try:
            date = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            return Response({"error_message": ["Invalid Date Format"]}, status=400)
        day_number = date.weekday() + 1
        regis = CourseRegistration.objects.select_related('course', 'teacher__school').prefetch_related(
            Prefetch(
                "teacher__unavailable_reg",
                queryset=UnavailableTimeRegular.objects.filter(
                    day=str(day_number)
                ).only("start", "stop"),
                to_attr="regular"
            ),
            Prefetch(
                "teacher__unavailable_once",
                queryset=UnavailableTimeOneTime.objects.filter(
                    date=date
                ).only("start", "stop"),
                to_attr="once"
            ),
        ).get(uuid=code)
        booked_lessons = Lesson.objects.filter(
            status="CON",
            registration__teacher=regis.teacher,
            booked_datetime__date=date
        ).annotate(time=Func(
            F('booked_datetime'),
            Value('HH:MM:SS'),
            function='to_char',
            output_field=CharField()
        )).values_list("time", flat=True)

        unavailable_regular = UnavailableTimeSerializer(regis.teacher.regular, many=True).data
        unavailable_times = UnavailableTimeSerializer(regis.teacher.once, many=True).data
        return Response(data={
            "booked_lessons": {
                "time": list(booked_lessons),
                "duration": regis.course.duration
            },
            "unavailable": list(unavailable_regular) + list(unavailable_times),
            "working": {
                "start": regis.teacher.school.start,
                "stop": regis.teacher.school.stop,
            }
        })
    
    def retrieve(self, request, code):
        filters = {
            "registration__uuid": code,
            "registration__student__user_id": request.user.id
        }
        lessons = Lesson.objects.filter(**filters)
        ser = ListLessonDateTimeSerializer(instance=lessons, many=True)
        return Response(ser.data, status=200)
    
    def create(self, request):
        data = dict(request.data)
        data["student_id"] = request.user.id
        ser = CourseRegistrationSerializer(data=data)
        if ser.is_valid():
            obj = ser.create(validated_data=ser.validated_data)
            return Response({"registration_id": obj.uuid}, status=200)
        else:
            return Response(ser.errors, status=400)

@permission_classes([IsAuthenticated])
class LessonViewset(ViewSet):
    def status(self, request, status):
        filters = {
            "registration__student__user_id": request.user.id
        }
        if status == "pending":
            filters['status'] = "PEN"
        elif status == "confirm":
            filters['status'] = "CON"
        try:
            lessons = Lesson.objects.select_related("registration__teacher__user", "registration__course").filter(**filters).order_by("booked_datetime")
        except ValidationError as e:
            return Response({"error_message": e}, status=400)
        ser = ListLessonSerializer(instance=lessons, many=True)
        return Response(ser.data, status=200)

    def recent(self, request):
        filters = {
            "registration__student__user_id": request.user.id
        }
        teacher_uuid = request.GET.get("teacher_uuid")
        if teacher_uuid:
            # Assuming you have a Teacher model with a UUID field
            teacher = get_object_or_404(Teacher, user__uuid=teacher_uuid)
            filters['registration__teacher_id'] = teacher.id
        lessons = Lesson.objects.select_related("registration__teacher__user", "registration__course").filter(**filters).order_by("booked_datetime")
        ser = ListLessonSerializer(instance=lessons, many=True)
        return Response(ser.data, status=200)

    def week(self, request):
        date = request.GET.get('date', None)
        if not date:
            return Response(status=400)
        date = datetime.strptime(date, '%Y-%m-%d')
        sw = date - timedelta(days=date.weekday())

        filters = {
            "registration__student__user_id": request.user.id,
            "booked_datetime__range": [sw, sw + timedelta(days=6)],
            }
        status = request.GET.get('status', None)
        if status == "pending":
            filters['status'] = "PEN"
        elif status == "confirm":
            filters['status'] = "CON"
        value = {}
        lessons = Lesson.objects.select_related("registration__student__user").filter(
                **filters
            ).order_by("booked_datetime")
        for i in range(7):
            filtlessons = [lesson for lesson in lessons if lesson.booked_datetime.date() == sw.date()]
            ser = ListLessonSerializer(instance=filtlessons, many=True)        
            value[sw.strftime('%Y-%m-%d')] = ser.data
            sw += timedelta(days=1)
        return Response(value)
    
    def day(self, request):
        date = request.GET.get('date', None)
        if not date:
            return Response(status=400)
        status = request.GET.get('status', None)
        filters = {
            "registration__student__user_id": request.user.id,
            "booked_datetime__date": date,
            }
        if status == "pending":
            filters['status'] = "PEN"
        elif status == "confirm":
            filters['status'] = "CON"
        lessons = Lesson.objects.select_related("registration__teacher__user", "registration__course").filter(
            **filters
        ).order_by("booked_datetime")
        ser = ListLessonSerializer(instance=lessons, many=True)
        return Response(ser.data)
    
    def create(self, request):
        data = dict(request.data)
        data["student_id"] = request.user.id
        ser = LessonSerializer(data=data)
        if ser.is_valid():
            obj = ser.create(validated_data=ser.validated_data)
            return Response({"booked_date": obj.booked_datetime}, status=200)
        else:
            return Response(ser.errors, status=400)
    
    def cancel(self, request, code):
        # Fetch the lesson object ensuring it belongs to the requesting user
        try:
            lesson = Lesson.objects.select_related("registration__teacher__user", "registration__course").get(code=code, registration__student__user__id=request.user.id)
        except Lesson.DoesNotExist:
            return Response({'success': "No Course Registration matches the given query."}, status=200)
        # Calculate the difference between now and the lesson's booked datetime
        now = timezone.now()
        time_difference = lesson.booked_datetime - now

        # Ensure the cancellation is at least 24 hours before the class
        if time_difference.total_seconds() >= 24 * 60 * 60:
            lesson.registration.used_lessons -= 1
            lesson.registration.save()
        lesson.status = 'CAN'
        lesson.save()
        
        devices = FCMDevice.objects.filter(user=lesson.registration.teacher.user_id)
        devices.send_message(
                message = Message(
                    notification=Notification(
                        title=f"{lesson.registration.course.name} Lesson Canceled!",
                        body=f'Your lesson with {request.user.first_name} has been canceled. We apologize for any inconvenience.'
                    ),
                ),
            )
        
        return Response({'success': 'Lesson canceled successfully.'}, status=200)
