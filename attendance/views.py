from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .models import Teacher

def home(request):
    return render(request, 'Authentication/Home_Page.html')

def login_page(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
                       
            if user.is_superuser or user.is_staff:
                return redirect('admin_dashboard')  
            else:
                return redirect('teacher_dashboard')  
        else:
            messages.error(request, 'Invalid username or password.')
            return render(request, 'Authentication/Login_Page.html')
    
    return render(request, 'Authentication/Login_Page.html')

def register_page(request):
    if request.method == 'POST':
       
        id_number = request.POST.get('id_number')
        role = request.POST.get('role')
        department = request.POST.get('department')
        last_name = request.POST.get('last_name')
        first_name = request.POST.get('first_name')
        middle_name = request.POST.get('middle_name')
        username = request.POST.get('username')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        security_question = request.POST.get('security_question')
        security_answer = request.POST.get('security_answer')
        
        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'Authentication/Register_Page.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return render(request, 'Authentication/Register_Page.html')
        
        if role == 'TEACHER' and Teacher.objects.filter(teacher_id=id_number).exists():
            messages.error(request, 'Teacher ID already exists.')
            return render(request, 'Authentication/Register_Page.html')
        
        user = User.objects.create_user(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )
        
        if role == 'TEACHER':
            Teacher.objects.create(
                user=user,
                teacher_id=id_number,
                first_name=first_name,
                last_name=last_name,
                middle_name=middle_name or '',
                age=0,
                sex='',
                birthday=None,
                email='',
                contact='',
                department=department,
                grade='',
                section='',
                security_question=security_question,
                security_answer=security_answer,
            )
        
        messages.success(request, 'Account created successfully!')
        return redirect('login')
    
    return render(request, 'Authentication/Register_Page.html')

def attendance_page(request):
    return render(request, 'Authentication/Attendance_Page.html')

#ADMIN
def admin_dashboard(request):
    return render(request, 'ADMIN/00_Dashboard.html')

def admin_users(request):
    return render(request, 'ADMIN/01_Users.html')

def admin_attendance(request):
    return render(request, 'ADMIN/02_Student_Attendance.html')

def admin_teachers(request):
    return render(request, 'ADMIN/03_Teachers_Info.html')

def admin_students(request):
    return render(request, 'ADMIN/04_Students_Info.html')

def admin_classes(request):
    return render(request, 'ADMIN/05_Classes.html')

def admin_register_rfid(request):
    return render(request, 'ADMIN/06_Register_RFID.html')

def admin_add_teacher(request):
    return render(request, 'ADMIN/07_Add_Teacher.html')

#TEACHER
def teacher_dashboard(request):
    return render(request, 'TEACHER/01_Dashboard.html')

def teacher_class_attendance(request):
    return render(request, 'TEACHER/02_Class_Attendance.html')

def teacher_class_record(request):
    return render(request, 'TEACHER/03_Class_Record.html')

def teacher_profile(request):
    return render(request, 'TEACHER/04_Personal_Info.html')

def teacher_security(request):
    return render(request, 'TEACHER/05_Security.html')