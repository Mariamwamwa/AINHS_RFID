from django.urls import path
from . import views

urlpatterns = [
    
    # =====================================================
    # AUTHENTICATION
    # =====================================================
    path('', views.home, name='home'),
    path('login/', views.login_page, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_page, name='register'),
    path('attendance/', views.attendance_page, name='attendance'),

    # =====================================================
    # PUBLIC RFID ATTENDANCE API
    # =====================================================
    path(
        'api/attendance/rfid/',
        views.record_rfid_attendance,
        name='record_rfid_attendance'
    ),

    # =====================================================
    # ADMIN
    # =====================================================
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/users/', views.admin_users, name='admin_users'),
    path('admin/teachers/', views.admin_teachers, name='admin_teachers'),
    path('admin/teachers/edit/<int:teacher_id>/', views.edit_teacher, name='edit_teacher'),
    path('admin/teachers/delete/<int:teacher_id>/', views.delete_teacher, name='delete_teacher'),
    path('admin/add-teacher/', views.admin_add_teacher, name='admin_add_teacher'),
    path('admin/classes/', views.admin_classes, name='admin_classes'),
    path('admin/classes/add/', views.add_class, name='add_class'),
    path('admin/classes/edit/<int:class_id>/', views.edit_class, name='edit_class'),
    path('admin/classes/delete/<int:class_id>/', views.delete_class, name='delete_class'),
    path('admin/students/', views.admin_students, name='admin_students'),
    path('admin/students/delete/<int:student_id>/', views.delete_student, name='delete_student'),
    path('admin/register-rfid/', views.admin_register_rfid, name='admin_register_rfid'),
    path('admin/attendance/', views.admin_attendance, name='admin_attendance'),

    # =====================================================
    # ADMIN — ATTENDANCE AJAX
    # =====================================================
    path('admin/attendance/save/', views.save_attendance, name='save_attendance'),
    path('admin/attendance/bulk/', views.bulk_attendance, name='bulk_attendance'),
    path('admin/attendance/reset/', views.reset_attendance, name='reset_attendance'),

    # =====================================================
    # TEACHER
    # =====================================================
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/profile/', views.teacher_profile, name='teacher_profile'),
    path('teacher/class-record/', views.teacher_class_record, name='teacher_class_record'),
    path('teacher/class-attendance/', views.teacher_class_attendance, name='teacher_class_attendance'),
    path('teacher/history/', views.teacher_history, name="teacher_history"),
    path('teacher/security/', views.teacher_security, name='teacher_security'),
    path('teacher/notifications/api/',views.teacher_notifications_api,name='teacher_notifications_api'),
    path('teacher/notifications/mark-read/',views.teacher_notifications_mark_read,name='teacher_notifications_mark_read'),
    path('teacher/security/change-password/',views.teacher_change_password,name='teacher_change_password'),
    path(
        'teacher/security/save/',
        views.teacher_save_security,
        name='teacher_save_security'
    ),
    path(
    'admin/students/edit/<int:student_id>/',
    views.edit_student,
    name='edit_student'
   ),
path(
    'admin/classes/assign/<int:class_id>/',
    views.assign_class,
    name='assign_class'
),

path(
    'admin/classes/unassign/<int:class_id>/',
    views.unassign_class,
    name='unassign_class'
),

path(
'teacher/attendance/export/daily/',
views.export_attendance_daily,
name='export_attendance_daily'
),

path(
'teacher/attendance/export/weekly/',
views.export_attendance_weekly,
name='export_attendance_weekly'
),

path(
'teacher/attendance/export/monthly/',
views.export_attendance_monthly,
name='export_attendance_monthly'
),

path(
    'admin/class-counts/',
    views.admin_class_counts,
    name='admin_class_counts'
),
    # =========================================================
# ADMIN NOTIFICATIONS
# =========================================================

path(
    "admin/notifications/",
    views.admin_notifications,
    name="admin_notifications"
),

path(
    "admin/notifications/read/",
    views.mark_admin_notifications_read,
    name="mark_admin_notifications_read"
),
]