from django.db import models
from school.models import Course, School
from core.models import User
from teacher.models import Teacher
from uuid import uuid4
from utils import generate_unique_code
import random
import string
# Create your models here.

class CourseRegistration(models.Model):
    STATUS_CHOICES = [
        ('PEN', 'Pending'),
        ('COM', 'Completed'),
        ('EXP', 'Expired'),
    ]
    uuid = models.UUIDField(default=uuid4, editable=False, unique=True)

    registered_date = models.DateField(auto_now_add=True)
    exp_date = models.DateField(null=True)
    finised_date = models.DateField(null=True, blank=True)

    status = models.CharField(choices=STATUS_CHOICES, max_length=3, default="PEN")
    used_lessons = models.IntegerField(default=0)

    student_favorite = models.BooleanField(default=False)
    teacher_favorite = models.BooleanField(default=False)

    teacher = models.ForeignKey(Teacher, on_delete=models.PROTECT)
    course = models.ForeignKey(to=Course, on_delete=models.PROTECT, related_name="registration")
    student = models.ForeignKey(to="Student", on_delete=models.CASCADE, related_name="registration")
    
    def __str__(self) -> str:
        return f"{self.student.__str__()} {self.course.__str__()} {self.teacher.__str__()}"


class StudentTeacherRelation(models.Model):
    student = models.ForeignKey("Student", on_delete=models.CASCADE, related_name="teacher_relation")
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name="student_relation")
    favorite_teacher = models.BooleanField(default=False)
    favorite_student = models.BooleanField(default=False)

class Student(models.Model):
    course = models.ManyToManyField(to=Course, through=CourseRegistration, related_name="student")
    school = models.ManyToManyField(to=School, related_name="student")
    teacher = models.ManyToManyField(to=Teacher, through=StudentTeacherRelation, related_name="student")
    user = models.OneToOneField(User, models.CASCADE)

    def __str__(self) -> str:
        return self.user.__str__()

class Lesson(models.Model):
    STATUS_CHOICES = [
        ('PENTE', 'PendingTeacher'),
        ('PENST', 'PendingStudent'),
        ('CON', 'Confirmed'),
        ('COM', 'Completed'),
        ('CAN', 'Canceled'),
        ('MIS', 'Missed'),
    ]

    notes = models.CharField(max_length=300, blank=True)
    booked_datetime = models.DateTimeField()
    registration = models.ForeignKey(to=CourseRegistration, on_delete=models.CASCADE, related_name="lesson")
    code = models.CharField(max_length=12, unique=True)
    status = models.CharField(choices=STATUS_CHOICES, max_length=5, default="PENTE")

    def generate_unique_code(self, length=8):
        """Generate a unique random code."""
        characters = string.ascii_letters + string.digits
        code = ''.join(random.choice(characters) for _ in range(length))
        return code
    
    def _generate_unique_code(self, length):
        """Generate a unique code and ensure it's not already in the database."""
        code = self.generate_unique_code(length)
        while Lesson.objects.filter(code=code).exists():
            code = self.generate_unique_code(length)
        return code
    
    def save(self, *args, **kwargs):
        if self.code is None or self.code == "":
            self.code = self._generate_unique_code(12)
        super(Lesson, self).save(*args, **kwargs)
        