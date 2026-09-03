from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Teacher(models.Model):
    DEPARTMENT_CHOICES = [
        ('SHS', 'Senior High School'),
        ('JHS', 'Junior High School'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile')
    teacher_id = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True, null=True)
    age = models.IntegerField()
    sex = models.CharField(max_length=10)
    birthday = models.DateField()
    email = models.EmailField()
    contact = models.CharField(max_length=20)
    department = models.CharField(max_length=10, choices=DEPARTMENT_CHOICES)
    grade = models.CharField(max_length=10)
    section = models.CharField(max_length=20)
    security_question = models.CharField(max_length=200)
    security_answer = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.last_name}, {self.first_name} ({self.teacher_id})"


class Student(models.Model):
    DEPARTMENT_CHOICES = [
        ('SHS', 'Senior High School'),
        ('JHS', 'Junior High School'),
    ]
    
    lrn = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True, null=True)
    age = models.IntegerField()
    sex = models.CharField(max_length=10)
    email = models.EmailField(blank=True, null=True)
    contact = models.CharField(max_length=20, blank=True, null=True)
    parent_name = models.CharField(max_length=200)
    parent_contact = models.CharField(max_length=20)
    department = models.CharField(max_length=10, choices=DEPARTMENT_CHOICES)
    grade = models.CharField(max_length=10)
    section = models.CharField(max_length=20)
    adviser = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, related_name='students')
    rfid = models.CharField(max_length=50, unique=True, blank=True, null=True)
    image = models.ImageField(upload_to='student_images/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.lrn} - {self.last_name}, {self.first_name}"


class Class(models.Model):
    DEPARTMENT_CHOICES = [
        ('SHS', 'Senior High School'),
        ('JHS', 'Junior High School'),
    ]
    
    department = models.CharField(max_length=10, choices=DEPARTMENT_CHOICES)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='classes')
    grade = models.CharField(max_length=10)
    section = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.grade} - {self.section} ({self.department})"


class Attendance(models.Model):
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('excused', 'Excused'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField(default=timezone.now)
    time_in_am = models.TimeField(blank=True, null=True)
    time_out_am = models.TimeField(blank=True, null=True)
    time_in_pm = models.TimeField(blank=True, null=True)
    time_out_pm = models.TimeField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='present')
    rfid_scanned = models.CharField(max_length=50, blank=True, null=True)
    scanned_by = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.student} - {self.date} ({self.status})"

    class Meta:
        unique_together = ('student', 'date')


class RFIDLog(models.Model):
    rfid = models.CharField(max_length=50)
    student = models.ForeignKey(Student, on_delete=models.SET_NULL, null=True, blank=True)
    scanned_at = models.DateTimeField(auto_now_add=True)
    action = models.CharField(max_length=20)
    status = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.rfid} - {self.scanned_at}"


class SystemLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=200)
    details = models.TextField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.action} - {self.created_at}"