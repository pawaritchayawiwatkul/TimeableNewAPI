from rest_framework.views import Response
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from student.models import CourseRegistration, Student, Lesson, StudentTeacherRelation
from teacher.models import UnavailableTimeOneTime, UnavailableTimeRegular, Teacher
from django.utils import timezone
from datetime import timedelta, datetime
from django.db.models import  Prefetch
from datetime import datetime
from django.core.exceptions import ValidationError
from student.serializers import ListLessonSerializer, CourseRegistrationSerializer, LessonSerializer, ListTeacherSerializer, ListCourseRegistrationSerializer, ListLessonDateTimeSerializer, ProfileSerializer
from django.shortcuts import get_object_or_404
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
    
    def destroy(self, request):
        request.user.delete()
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
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            return Response({"error_message": ["Invalid Date Format"]}, status=400)
        day_number = date_obj.weekday() + 1
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
                    date=date_obj
                ).only("start", "stop"),
                to_attr="once"
            ),
        ).get(uuid=code)
        booked_lessons = Lesson.objects.filter(
            status__in=["CON", "PENTE", "PENST"],
            registration__teacher=regis.teacher,
            booked_datetime__date=date_obj
        )

        unavailables = regis.teacher.regular + regis.teacher.once
        duration = timedelta(minutes=regis.course.duration)
        interval = timedelta(minutes=30)

        available_times = []
        current_time = timezone.make_aware(datetime.combine(date_obj, regis.teacher.school.start))
        stop_time = timezone.make_aware(datetime.combine(date_obj, regis.teacher.school.stop))
        while current_time + duration <= stop_time:
            end_time = current_time + duration
            
            is_available = True
            for unavailable in unavailables:
                start_ = timezone.make_aware(datetime.combine(date_obj, unavailable.start))
                stop_ = timezone.make_aware(datetime.combine(date_obj, unavailable.stop))
                if (start_ <= current_time < stop_) or (start_ < end_time <= stop_):
                    is_available = False
                    break
            for lesson in booked_lessons:
                start_ = lesson.booked_datetime
                stop_ = start_ + timedelta(minutes=regis.course.duration)
                if (start_ <= current_time < stop_) or (start_ < end_time <= stop_):
                    is_available = False
                    break
            if is_available:
                available_times.append({
                    "start": current_time.strftime("%H:%M:%S"),
                    "end": end_time.strftime("%H:%M:%S")
                })
            
            current_time += interval

        return Response(data={
            "availables":available_times
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
    def confirm(self, request, code):
        try:
            lesson = Lesson.objects.select_related("registration__course", "registration__teacher").get(code=code, registration__student__user__id=request.user.id, status="PENST")
        except Lesson.DoesNotExist:
            return Response({'failed': "No Lesson matches the given query."}, status=200)
        lesson.status = 'CON'
        lesson.save()

        devices = FCMDevice.objects.filter(user_id=lesson.registration.teacher.user_id)
        devices.send_message(
                message =Message(
                    notification=Notification(
                        title=f"Lesson Confirmed",
                        body=f'{request.user.first_name} on {lesson.booked_datetime.strftime("%Y-%m-%d")} at {lesson.booked_datetime.strftime("%H:%M")}.'
                    ),
                ),
            )
        
        return Response({'success': 'Lesson confirmed successfully.'}, status=200)
    
    def status(self, request, status):
        filters = {
            "registration__student__user_id": request.user.id
        }
        if status == "pending":
            filters['status__in'] = ["PENTE", "PENST"]
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
            filters['status__in'] = ["PENTE", "PENST"]
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
            filters['status__in'] = ["PENTE", "PENST"]
        elif status == "confirm":
            filters['status'] = "CON"
        lessons = Lesson.objects.select_related("registration__teacher__user", "registration__course").filter(
            **filters
        ).order_by("booked_datetime")
        ser = ListLessonSerializer(instance=lessons, many=True)
        return Response(ser.data)
    
    def list(self, request):
        filters = {
            "registration__student__user_id": request.user.id,
            }
        
        date = request.GET.get('date', None)
        if date:
            date = datetime.strptime(date, '%Y-%m-%d')
            filters['booked_datetime__gte'] = date
        
        status = request.GET.get('status', None)
        if status == "pending":
            filters['status__in'] = ["PENTE", "PENST"]
        elif status == "confirm":
            filters['status'] = "CON"
        lessons = Lesson.objects.select_related("registration__teacher__user").filter(
                **filters
            ).order_by("booked_datetime")
        ser = ListLessonSerializer(instance=lessons, many=True)
        return Response(ser.data)
        
    def create(self, request):
        data = dict(request.data)
        data["student_id"] = request.user.id
        registration_id = data.pop("registration_id")
        booked_date = datetime.strptime(data["booked_datetime"], "%Y-%m-%dT%H:%M:%SZ")
        day_number = booked_date.weekday() + 1
        try:
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
                            date=booked_date
                        ).only("start", "stop"),
                        to_attr="once"
                    ),
                ).get(uuid=registration_id, student__user_id=request.user.id)
            data['registration'] = regis.pk
        except CourseRegistration.DoesNotExist:
            return Response({"error": "Invalid Course UUID"}, status=400)
        ser = LessonSerializer(data=data)
        if ser.is_valid():
            booked_lessons = Lesson.objects.filter(
                status__in=["CON", "PENTE", "PENST"],
                registration__teacher=regis.teacher,
                booked_datetime__date=booked_date
            )
            unavailables = regis.teacher.regular + regis.teacher.once
            start_time = timezone.make_aware(booked_date)
            end_time = start_time + timedelta(minutes=regis.course.duration)
            school_start = timezone.make_aware(datetime.combine(start_time, regis.course.school.start))
            school_close = timezone.make_aware(datetime.combine(start_time, regis.course.school.stop))
            if not (school_start <= start_time < school_close) or not (school_start <= end_time <= school_close):
                return Response({"error": "Not in operating Time"}, status=400)
            for unavailable in unavailables:
                start_ = timezone.make_aware(datetime.combine(start_time, unavailable.start))
                stop_ = timezone.make_aware(datetime.combine(start_time, unavailable.stop))
                if (start_ <= start_time < stop_) or (start_ < end_time <= stop_):
                    return Response({"error": "Invalid Time"}, status=400)
            for lesson in booked_lessons:
                start_ = lesson.booked_datetime
                stop_ = start_ + timedelta(minutes=regis.course.duration)
                print(start_, stop_)
                # print(start_time, end_time)
                if (start_ <= start_time < stop_) or (start_ < end_time <= stop_):
                    return Response({"error": "Invalid Time s"}, status=400)
            obj = ser.create(validated_data=ser.validated_data)

            devices = FCMDevice.objects.filter(user_id=regis.teacher.user_id)
            devices.send_message(
                    message=Message(
                        notification=Notification(
                            title=f"Lesson Requested!",
                            body=f'{request.user.first_name} on {obj.booked_datetime.strftime("%Y-%m-%d")} at {obj.booked_datetime.strftime("%H:%M")}.'
                        ),
                    ),
                )
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
        
        devices = FCMDevice.objects.filter(user_id=lesson.registration.teacher.user_id)
        devices.send_message(
                message = Message(
                    notification=Notification(
                        title=f"Lesson Canceled",
                        body=f'{request.user.first_name} on {lesson.booked_datetime.strftime("%Y-%m-%d")} at {lesson.booked_datetime.strftime("%H:%M")}.'
                    ),
                ),
            )
        
        return Response({'success': 'Lesson canceled successfully.'}, status=200)
