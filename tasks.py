from student.models import CourseRegistration
from django.utils import timezone

def twenty_seconds():
    today = timezone.now().date()
    registrations = CourseRegistration.objects.filter(exp_date__lt=today)
    for registration in registrations:
        registration.status = "EXP"
    CourseRegistration.objects.bulk_update(registrations, "status")
    print("RUNNING EVERY 20 SECONDS")