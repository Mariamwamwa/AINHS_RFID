from django.urls import path
from . import views

urlpatterns = [
    
    path('', views.home, name='home'),
    path('login/', views.login_page, name='login'),
    path('register/', views.register_page, name='register'),
    path('attendance/', views.attendance_page, name='attendance'),
  
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/users/', views.admin_users, name='admin_users'),
    path('admin/teachers/', views.admin_teachers, name='admin_teachers'),
    path('admin/add-teacher/', views.admin_add_teacher, name='admin_add_teacher'),
    path('admin/classes/', views.admin_classes, name='admin_classes'),
    path('admin/students/', views.admin_students, name='admin_students'),
    path('admin/register-rfid/', views.admin_register_rfid, name='admin_register_rfid'),
    path('admin/attendance/', views.admin_attendance, name='admin_attendance'),
    
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/profile/', views.teacher_profile, name='teacher_profile'),
    path('teacher/class-record/', views.teacher_class_record, name='teacher_class_record'),
    path('teacher/class-attendance/', views.teacher_class_attendance, name='teacher_class_attendance'),
    path('teacher/security/', views.teacher_security, name='teacher_security'),
]