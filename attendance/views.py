from django.shortcuts import render

def home(request):
    return render(request, 'Authentication/Home_Page.html')

def login_page(request):
    return render(request, 'Authentication/Login_Page.html')

def register_page(request):
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