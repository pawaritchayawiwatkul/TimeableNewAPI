from celery import shared_task
from django.core.mail import send_mail
from student.models import Lesson, GuestLesson
from datetime import timedelta
from django.utils import timezone
from pytz import timezone as ptimezone
from utils import send_notification
from celery_singleton import Singleton


_timezone = timezone.get_current_timezone()
print(_timezone)
utc_timezone = ptimezone('UTC')

# Send Notifications
@shared_task(base=Singleton)
def send_lesson_notification():
    now = timezone.now()
    now = now + timedelta(hours=7)
    end_time = now + timedelta(minutes=60)
    upcoming_lessons = list(Lesson.objects.select_related("registration__student__user", "registration__teacher__user").filter(
        booked_datetime__gte=now,
        booked_datetime__lte=end_time,
        status='CON',
        notified=False
    ))
    if upcoming_lessons:
        for lesson in upcoming_lessons:
            send_notification(
                lesson.registration.student.user_id, 
                "Lesson Notification", 
                f'You have a lesson with {lesson.registration.teacher.user.first_name} on {lesson.booked_datetime.strftime("%Y-%m-%d")} at {lesson.booked_datetime.strftime("%H:%M")}.')
            send_notification(
                lesson.registration.teacher.user_id, 
                "Lesson Notification",  
                f'You have a lesson with {lesson.registration.student.user.first_name} on {lesson.booked_datetime.strftime("%Y-%m-%d")} at {lesson.booked_datetime.strftime("%H:%M")}.')
            lesson.notified = True
            
        Lesson.objects.bulk_update(upcoming_lessons, fields=["notified"])
    return len(upcoming_lessons)

@shared_task(base=Singleton)
def send_guest_lesson_notification():
    now = timezone.now()
    now = now + timedelta(hours=7)
    end_time = now + timedelta(minutes=60)
    upcoming_guest_lessons = list(GuestLesson.objects.select_related("teacher__user").filter(
        datetime__gte=now,
        datetime__lte=end_time,
        status='CON',
        notified=False
    ))
    if upcoming_guest_lessons:
        for lesson in upcoming_guest_lessons:
            send_notification(
                lesson.teacher.user_id, 
                "Lesson Notification",  
                f'You have a lesson with {lesson.name} on {lesson.datetime.strftime("%Y-%m-%d")} at {lesson.datetime.strftime("%H:%M")}.')
            send_mail(
                "Lesson Notification", 
                f'You have a lesson with {lesson.teacher.user.first_name} on {lesson.datetime.strftime("%Y-%m-%d")} at {lesson.datetime.strftime("%H:%M")}.',
                "hello.timeable@gmail.com", 
                [lesson.email], 
                fail_silently=True)
            lesson.notified = True
            
        GuestLesson.objects.bulk_update(upcoming_guest_lessons, fields=["notified"])