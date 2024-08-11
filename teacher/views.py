from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import permission_classes
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from teacher.models import Teacher, TeacherCourses
from teacher.serializers import SchoolSerializer, UnavailableTimeSerializer, LessonSerializer, TeacherCourseDetailwithStudentSerializer, TeacherCourseDetailSerializer, RegularUnavailableSerializer, OnetimeUnavailableSerializer, UnavailableTimeOneTime, UnavailableTimeRegular, TeacherCourseListSerializer, CourseSerializer, ProfileSerializer, ListStudentSerializer, ListCourseRegistrationSerializer, ListLessonDateTimeSerializer, CourseRegistrationSerializer, ListLessonSerializer
from student.models import Student, StudentTeacherRelation, CourseRegistration, Lesson
from school.models import School
from django.core.exceptions import ValidationError
from rest_framework.views import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from django.db.models import Prefetch
from utils import merge_schedule
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Count, F, Func, Value, CharField, Prefetch
from fcm_django.models import FCMDevice
from firebase_admin.messaging import Message, Notification
import boto3
from botocore.exceptions import ClientError
import os

@permission_classes([IsAuthenticated])
class UnavailableTimeViewset(ViewSet):
    def one_time(self, request):
        data = request.data
        data['user_id'] = request.user.id
        ser = OnetimeUnavailableSerializer(data=data)
        if ser.is_valid():
            date = ser.validated_data['date']
            teacher_id = ser.validated_data['teacher_id']
            unavailables = list(UnavailableTimeOneTime.objects.filter(date=date, teacher_id=teacher_id).only("start", "stop"))
            validated_data, overlap = merge_schedule(ser.validated_data, unavailables)
            ids_to_delete = [int(instance.id) for instance in overlap]
            UnavailableTimeOneTime.objects.filter(id__in=ids_to_delete).delete()
            ser.create(validated_data)
            return Response(ser.data, status=200)
        return Response(ser.errors, status=400)
    
    def regular(self, request):
        data = request.data
        data['user_id'] = request.user.id
        days = data['day']
        for day in days:
            data['day'] = day
            ser = RegularUnavailableSerializer(data=data)
            if ser.is_valid():
                day = ser.validated_data['day']
                teacher_id = ser.validated_data['teacher_id']
                unavailables = list(UnavailableTimeRegular.objects.filter(day=day, teacher_id=teacher_id).only("start", "stop"))
                validated_data, overlap = merge_schedule(ser.validated_data, unavailables)
                ids_to_delete = [int(instance.id) for instance in overlap]
                UnavailableTimeRegular.objects.filter(id__in=ids_to_delete).delete()
                ser.create(validated_data)
            else:
                return Response(ser.errors, status=400)
        return Response(status=200)

    def retrieve(self, request):
        date = request.GET.get("date", None)
        if not date:
            return Response(status=400)
        date = datetime.strptime(date, '%Y-%m-%d')
        day_number = date.weekday() + 1
        teacher = Teacher.objects.prefetch_related(
            Prefetch(
                "unavailable_reg",
                queryset=UnavailableTimeRegular.objects.filter(
                    day=str(day_number)
                ).only("start", "stop"),
                to_attr="regular"
            ),
            Prefetch(
                "unavailable_once",
                queryset=UnavailableTimeOneTime.objects.filter(
                    date=date
                ).only("start", "stop"),
                to_attr="once"
            ),
        ).get(user__id=request.user.id)

        unavailable_regular = UnavailableTimeSerializer(teacher.regular, many=True).data
        unavailable_times = UnavailableTimeSerializer(teacher.once, many=True).data
        return Response(data={
            "unavailable": list(unavailable_regular) + list(unavailable_times),
        })

    def remove(self, request, code):
        try:
            UnavailableTimeRegular.objects.get(code=code, teacher__user_id=request.user.id)
        except UnavailableTimeRegular.DoesNotExist:
            try:
                UnavailableTimeOneTime.objects.get(code=code, teacher__user_id=request.user.id)
            except UnavailableTimeOneTime.DoesNotExist:
                return Response(status=400)

        return Response()
    
@permission_classes([IsAuthenticated])
class CourseViewset(ViewSet):
    def favorite(self, request, code):
        fav = request.GET.get("fav", None)
        if fav in ["0", "1"]:
            fav = bool(int(fav))
            regis = get_object_or_404(TeacherCourses, course__uuid=code, teacher__user_id=request.user.id)
            regis.favorite = bool(int(fav))
            regis.save()
            return Response({"favorite": fav}, status=200)
        else:
            return Response({"error_messages": ["Invalid Request"]}, status=400)
        
    def list(self, request):
        teacher_course = TeacherCourses.objects.select_related("course").filter(teacher__user_id=request.user.id)
        ser = TeacherCourseListSerializer(instance=teacher_course, many=True)
        return Response(ser.data)
    
    def create(self, request):
        data = dict(request.data)
        data["user_id"] = request.user.id
        ser = CourseSerializer(data=data)
        if ser.is_valid():
            ser.create(validated_data=ser.validated_data)
            return Response(ser.data, status=200)
        else:
            return Response(ser.errors, status=400)
    
    def retrieve(self, request, code):
        try:
            tcourse = TeacherCourses.objects.select_related("course").prefetch_related(Prefetch('course__registration')).get(teacher__user_id=request.user.id, course__uuid=code)
            # tcourse = TeacherCourses.objects.select_related("course").prefetch_related(Prefetch('course__registration')).annotate(
            #     number_of_registered=Count('course__registration', distinct=True),
            #     number_of_student=Count('course__registration__student', distinct=True),
            #     number_of_comlesson=Count('course__registration__lesson', filter=Q(course__registration__lesson__status='COM'), distinct=True)  # Count completed lessons related to course registrations
            # ).get(teacher__user_id=request.user.id, course__uuid=code)
        except TeacherCourses.DoesNotExist:
            return Response({"error_messages": ["Invalid UUID"]}, status=400)
        ser = TeacherCourseDetailSerializer(instance=tcourse)
        return Response(ser.data)

    def retrieve_with_student(self, request, code):
        try:
            tcourse = TeacherCourses.objects.select_related("course").prefetch_related(Prefetch('course__registration')).get(teacher__user_id=request.user.id, course__uuid=code)
        except TeacherCourses.DoesNotExist:
            return Response({"error_messages": ["Invalid UUID"]}, status=400)
        ser = TeacherCourseDetailwithStudentSerializer(instance=tcourse)
        return Response(ser.data)
    
@permission_classes([IsAuthenticated])
class ProfileViewSet(ViewSet):
    def retrieve(self, request):
        user = request.user
        try:
            ser = ProfileSerializer(instance=user)
            return Response(ser.data)
        except Teacher.DoesNotExist:
            return Response(status=404)
    
    def update(self, request):
        user = request.user
        ser = ProfileSerializer(data=request.data)
        if ser.is_valid():
            user = ser.update(user, ser.validated_data)
            return Response(status=200)
        else:
            return Response(ser.errors, status=400)
        
@permission_classes([IsAuthenticated])
class SchoolViewSet(ViewSet):
    def retrieve(self, request):
        user = request.user
        try:
            teacher = Teacher.objects.select_related("school").get(user_id=user.id)
            ser = SchoolSerializer(instance=teacher.school)
            return Response(ser.data)
        except Teacher.DoesNotExist:
            return Response(status=404)
        
    def update(self, request):
        ser = SchoolSerializer(data=request.data)
        try:
            teacher = Teacher.objects.select_related("school").get(user_id=request.user.id).school
        except:
            return Response(status=404)
        if ser.is_valid():
            school = ser.update(teacher, ser.validated_data)
            return Response(ser.data, status=200)
        else: 
            return Response(ser.errors, status=400)
        

@permission_classes([IsAuthenticated])
class StudentViewset(ViewSet):
    def add(self, request, code):
        student = get_object_or_404(Student, user__uuid=code)
        user = request.user
        teacher = get_object_or_404(Teacher, user_id=user.id)
        if not student.teacher.filter(id=student.id).exists():
            student.teacher.add(teacher)
            student.school.add(teacher.school_id)
        return Response(status=200)
    
    def list(self, request):
        students = StudentTeacherRelation.objects.select_related("student__user").filter(teacher__user_id=request.user.id)
        ser = ListStudentSerializer(instance=students, many=True)
        return Response(ser.data)
    
    def favorite(self, request, code):
        fav = request.GET.get("fav", None)
        if fav in ["0", "1"]:
            fav = bool(int(fav))
            regis = get_object_or_404(StudentTeacherRelation, student__user__uuid=code, teacher__user_id=request.user.id)
            regis.favorite = bool(int(fav))
            regis.save()
            return Response({"favorite": fav}, status=200)
        else:
            return Response({"error_messages": ["Invalid Request"]}, status=400)
    
@permission_classes([IsAuthenticated]) 
class RegistrationViewset(ViewSet):
    def favorite(self, request, code):
        fav = request.GET.get("fav", None)
        if fav in ["0", "1"]:
            fav = bool(int(fav))
            regis = get_object_or_404(CourseRegistration, uuid=code, teacher__user_id=request.user.id)
            regis.favorite = bool(int(fav))
            regis.save()
            return Response({"favorite": fav}, status=200)
        else:
            return Response({"error_messages": ["Invalid Request"]}, status=400)
        
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
            "start": regis.teacher.school.start,
            "stop": regis.teacher.school.stop,
        })
    

    def list(self, request):
        filters = {
            'teacher__user_id': request.user.id,
        }
        student_uuid = request.GET.get("student_uuid")
        if student_uuid:
            # Assuming you have a Teacher model with a UUID field
            student = get_object_or_404(Student, user__uuid=student_uuid)
            filters['student'] = student

        courses = CourseRegistration.objects.select_related("course").filter(**filters)
        ser = ListCourseRegistrationSerializer(instance=courses, many=True)
        return Response(ser.data)
    
    def retrieve(self, request, code):
        filters = {
            "registration__uuid": code,
            "registration__teacher__user_id": request.user.id
        }
        lessons = Lesson.objects.select_related("registration__student__user", "registration__course").filter(**filters)
        ser = ListLessonSerializer(instance=lessons, many=True)
        return Response(ser.data, status=200)
    
    def create(self, request):
        data = dict(request.data)
        data["teacher_id"] = request.user.id
        ser = CourseRegistrationSerializer(data=data)
        if ser.is_valid():
            obj = ser.create(validated_data=ser.validated_data)
            return Response({"registration_id": obj.uuid}, status=200)
        else:
            return Response(ser.errors, status=400)

@permission_classes([IsAuthenticated])
class LessonViewset(ViewSet):
    def cancel(self, request, code):
        try:
            lesson = Lesson.objects.select_related("registration").get(code=code, registration__teacher__user__id=request.user.id)
        except Lesson.DoesNotExist:
            return Response({'failed': "No Lesson matches the given query."}, status=200)

        now = timezone.now()
        time_difference = lesson.booked_datetime - now

        if time_difference.total_seconds() >= 24 * 60 * 60:
            lesson.registration.used_lessons -= 1
            lesson.registration.save()
        lesson.status = 'CAN'
        lesson.save()
        
        devices = FCMDevice.objects.filter(user=lesson.registration.student.user_id)
        devices.send_message(
                message = Message(
                    notification=Notification(
                        title=f"{lesson.registration.course.name} Lesson Canceled!",
                        body=f'Your lesson with {request.user.first_name} has been canceled. We apologize for any inconvenience.'
                    ),
                ),
            )
        
        return Response({'success': 'Lesson canceled successfully.'}, status=200)
    
    def confirm(self, request, code):
        try:
            lesson = Lesson.objects.select_related("registration__course", "registration__student").get(code=code, registration__teacher__user__id=request.user.id, status="PEN")
        except Lesson.DoesNotExist:
            return Response({'failed': "No Lesson matches the given query."}, status=200)
        lesson.status = 'CON'
        lesson.save()

        devices = FCMDevice.objects.filter(user=lesson.registration.student.user_id)
        devices.send_message(
                message =Message(
                    notification=Notification(
                        title=f"{lesson.registration.course.name} Lesson Confirmed!",
                        body=f'Your lesson with {request.user.first_name} on [Date] at [Time] has been confirmed. Get ready to learn and excel!'
                    ),
                ),
            )
        
        return Response({'success': 'Lesson confirmed successfully.'}, status=200)
    
    def attended(self, request, code):
        try:
            lesson = Lesson.objects.select_related("registration__course", "registration__student").get(code=code, registration__teacher__user__id=request.user.id, status="CON")
        except Lesson.DoesNotExist:
            return Response({'failed': "No Lesson matches the given query."}, status=200)
    
        if lesson.booked_datetime >= timezone.now():
            return Response({'failed': "Has Not passed Booked Datetime."}, status=200)
        
        lesson.status = 'COM'
        lesson.save()
        lesson.registration.used_lessons += 1
        lesson.registration.save()

        devices = FCMDevice.objects.filter(user=lesson.registration.student.user_id)
        devices.send_message(
                message =Message(
                    notification=Notification(
                        title=f"{lesson.registration.course.name} Lesson Attended!",
                        body=f'Your lesson with {request.user.first_name} on [Date] at [Time] has been attended.'
                    ),
                ),
            )
        
        return Response({'success': 'Lesson attended successfully.'}, status=200)
    
    def missed(self, request, code):
        try:
            lesson = Lesson.objects.select_related("registration__course", "registration__student").get(code=code, registration__teacher__user__id=request.user.id, status="CON")
        except Lesson.DoesNotExist:
            return Response({'failed': "No Lesson matches the given query."}, status=200)
    
        if lesson.booked_datetime >= timezone.now():
            return Response({'failed': "Has Not passed Booked Datetime."}, status=200)

        lesson.status = 'MIS'
        lesson.save()

        devices = FCMDevice.objects.filter(user=lesson.registration.student.user_id)
        devices.send_message(
                message =Message(
                    notification=Notification(
                        title=f"{lesson.registration.course.name} Lesson Missed!",
                        body=f'Your missed a lesson with {request.user.first_name} on [Date] at [Time].'
                    ),
                ),
            )
        
        return Response({'success': 'Lesson marked as missed.'}, status=200)
        
    def status(self, request, status):
        filters = {
            "registration__teacher__user_id": request.user.id
        }
        if status == "pending":
            filters['status'] = "PEN"
        elif status == "confirm":
            filters['status'] = "CON"
        try:
            lessons = Lesson.objects.select_related("registration__student__user", "registration__course").filter(**filters).order_by("booked_datetime")
        except ValidationError as e:
            return Response({"error_message": e}, status=400)
        ser = ListLessonSerializer(instance=lessons, many=True)
        return Response(ser.data, status=200)
    
    def recent(self, request):
        filters = {
            "registration__teacher__user_id": request.user.id
        }
        registration_uuid = request.GET.get("registration_uuid")
        if registration_uuid:
            filters['registration__uuid'] = registration_uuid
        lessons = Lesson.objects.select_related("registration__student__user", "registration__course").filter(**filters).order_by("booked_datetime")
        ser = ListLessonSerializer(instance=lessons, many=True)
        return Response(ser.data, status=200)
    
    def week(self, request):
        date = request.GET.get('date', None)
        if not date:
            return Response(status=400)
        date = datetime.strptime(date, '%Y-%m-%d')
        sw = date - timedelta(days=date.weekday())

        filters = {
            "registration__teacher__user_id": request.user.id,
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
        for i in range(6):
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
            "registration__teacher__user_id": request.user.id,
            "booked_datetime__date": date,
            }
        if status == "pending":
            filters['status'] = "PEN"
        elif status == "confirm":
            filters['status'] = "CON"
        lessons = Lesson.objects.select_related("registration__student__user").filter(
            **filters
        ).order_by("booked_datetime")
        ser = ListLessonSerializer(instance=lessons, many=True)
        return Response(ser.data)

    def create(self, request):
        data = dict(request.data)
        data["teacher_id"] = request.user.id
        ser = LessonSerializer(data=data)
        if ser.is_valid():
            obj = ser.create(validated_data=ser.validated_data)
            return Response({"booked_date": obj.booked_datetime}, status=200)
        else:
            return Response(ser.errors, status=400)
        