import json
from datetime import date as date_cls, time as time_cls

from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.db import transaction
from django.db.models import Q
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from django.http import HttpResponse
from datetime import timedelta
from .models import Admin, Teacher, Student, Class, Attendance, Notification


# =====================================================
# HELPER — GET ADMIN DEPARTMENT & GRADE FILTER
# =====================================================

def get_admin_department(request):
    """Return 'JHS', 'SHS', or None (superuser)."""
    if request.user.is_superuser:
        return None

    try:
        return request.user.admin_profile.department
    except (AttributeError, Admin.DoesNotExist):
        return None


def get_teacher(request):
    """Return Teacher object or None."""
    try:
        return request.user.teacher_profile
    except Teacher.DoesNotExist:
        return None


# =====================================================
# AUTHENTICATION
# =====================================================

def home(request):
    return render(request, 'AUTHENTICATION/Home_Page.html')


def login_page(request):

    if request.method == 'POST':

        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        role = (request.POST.get('role') or '').lower()

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            if role == 'admin':

                if user.is_superuser or user.is_staff:
                    login(request, user)
                    return redirect('admin_dashboard')

                messages.error(
                    request,
                    'You are not authorized as admin.'
                )

                return redirect('login')

            elif role == 'teacher':

                try:

                    Teacher.objects.get(
                        user=user
                    )

                    login(request, user)

                    return redirect(
                        'teacher_dashboard'
                    )

                except Teacher.DoesNotExist:

                    messages.error(
                        request,
                        'No teacher profile found.'
                    )

                    return redirect('login')

            else:

                messages.error(
                    request,
                    'Please select an account type.'
                )

                return redirect('login')

        else:

            messages.error(
                request,
                'Invalid username or password.'
            )

            return render(
                request,
                'AUTHENTICATION/Login_Page.html'
            )

    return render(
        request,
        'AUTHENTICATION/Login_Page.html'
    )


def logout_view(request):

    logout(request)

    messages.success(
        request,
        'You have been logged out.'
    )

    return redirect('login')


def register_page(request):

    if request.method == 'POST':

        id_number = request.POST.get(
            'id_number',
            ''
        ).strip()

        role = (
            request.POST.get('role') or ''
        ).upper()

        department = (
            request.POST.get(
                'department',
                ''
            )
            .strip()
            .upper()
        )

        last_name = request.POST.get(
            'last_name',
            ''
        ).strip()

        first_name = request.POST.get(
            'first_name',
            ''
        ).strip()

        middle_name = request.POST.get(
            'middle_name',
            ''
        ).strip()

        username = request.POST.get(
            'username',
            ''
        ).strip()

        password = request.POST.get(
            'password',
            ''
        )

        confirm_password = request.POST.get(
            'confirm_password',
            ''
        )

        security_question = request.POST.get(
            'security_question',
            ''
        )

        security_answer = request.POST.get(
            'security_answer',
            ''
        ).strip()

        age = request.POST.get('age') or None

        sex = request.POST.get(
            'sex',
            ''
        )

        birthday = request.POST.get(
            'birthday'
        ) or None

        email = request.POST.get(
            'email',
            ''
        )

        contact = request.POST.get(
            'contact',
            ''
        )

        if password != confirm_password:

            messages.error(
                request,
                'Passwords do not match.'
            )

            return render(
                request,
                'AUTHENTICATION/Register_Page.html'
            )

        if department not in ('JHS', 'SHS'):

            messages.error(
                request,
                'Please select a valid department.'
            )

            return render(
                request,
                'AUTHENTICATION/Register_Page.html'
            )

        if User.objects.filter(
            username=username
        ).exists():

            messages.error(
                request,
                'Username already exists.'
            )

            return render(
                request,
                'AUTHENTICATION/Register_Page.html'
            )

        if (
            role == 'TEACHER'
            and
            Teacher.objects.filter(
                teacher_id=id_number
            ).exists()
        ):

            messages.error(
                request,
                'Teacher ID already exists.'
            )

            return render(
                request,
                'AUTHENTICATION/Register_Page.html'
            )

        if (
            role == 'ADMIN'
            and
            Admin.objects.filter(
                admin_id=id_number
            ).exists()
        ):

            messages.error(
                request,
                'Admin ID already exists.'
            )

            return render(
                request,
                'AUTHENTICATION/Register_Page.html'
            )

        if role == 'ADMIN':

            user = User.objects.create_user(
                username=username,
                password=password,
                first_name=first_name,
                last_name=last_name,
                email=email or '',
                is_staff=True,
                is_superuser=False,
            )

        else:

            user = User.objects.create_user(
                username=username,
                password=password,
                first_name=first_name,
                last_name=last_name,
                email=email or '',
                is_staff=False,
                is_superuser=False,
            )

        if role == 'ADMIN':

            Admin.objects.create(
                user=user,
                admin_id=id_number,
                first_name=first_name,
                last_name=last_name,
                middle_name=middle_name or '',
                department=department,
                security_question=security_question,
                security_answer=make_password(
                    security_answer
                ),
                plain_password=password,
                plain_security_answer=security_answer,
            )

        elif role == 'TEACHER':

            Teacher.objects.create(
                user=user,
                teacher_id=id_number,
                first_name=first_name,
                last_name=last_name,
                middle_name=middle_name or '',
                age=int(age) if age else None,
                sex=sex or '',
                birthday=birthday,
                email=email or '',
                contact=contact or '',
                department=department,
                security_question=security_question,
                security_answer=make_password(
                    security_answer
                ),
                plain_password=password,
                plain_security_answer=security_answer,
            )

        messages.success(
            request,
            'Account created successfully!'
        )

        return redirect('login')

    return render(
        request,
        'AUTHENTICATION/Register_Page.html'
    )


def attendance_page(request):

    return render(
        request,
        'AUTHENTICATION/Attendance_Page.html'
    )


# =====================================================
# PUBLIC RFID ATTENDANCE
# =====================================================

@csrf_exempt
@require_http_methods(["POST"])
def record_rfid_attendance(request):

    # =================================================
    # READ JSON
    # =================================================

    try:

        payload = json.loads(
            request.body
        )

    except (
        json.JSONDecodeError,
        TypeError
    ):

        return JsonResponse(
            {
                'success': False,
                'error': 'Invalid JSON.'
            },
            status=400
        )

    # =================================================
    # GET RFID
    # =================================================

    rfid = str(
        payload.get(
            'rfid',
            ''
        )
    ).strip()

    if not rfid:

        return JsonResponse(
            {
                'success': False,
                'error': 'RFID is required.'
            },
            status=400
        )

    # =================================================
    # CURRENT SERVER DATE AND TIME
    # =================================================

    now = timezone.localtime()

    current_date = now.date()

    current_time = now.time()

    # =================================================
    # ATTENDANCE TIME WINDOWS
    # =================================================

    AM_IN_START = time_cls(6, 10)

    AM_OUT_START = time_cls(10, 12)

    PM_IN_START = time_cls(12, 2)

    PM_OUT_START = time_cls(14, 1)

    # =================================================
    # DETERMINE ATTENDANCE FIELD + LABEL
    # =================================================

    if current_time < AM_IN_START:

        return JsonResponse(
            {
                'success': False,

                'error': (
                    'AM attendance has not started yet. '
                    'AM TIME IN starts at 6:10 AM.'
                )
            },
            status=400
        )

    elif (
        AM_IN_START
        <= current_time
        < AM_OUT_START
    ):

        target_field = 'time_in_am'

        attendance_label = 'AM TIME IN'

    elif (
        AM_OUT_START
        <= current_time
        < PM_IN_START
    ):

        target_field = 'time_out_am'

        attendance_label = 'AM TIME OUT'

    elif (
        PM_IN_START
        <= current_time
        < PM_OUT_START
    ):

        target_field = 'time_in_pm'

        attendance_label = 'PM TIME IN'

    else:

        target_field = 'time_out_pm'

        attendance_label = 'PM TIME OUT'

    # =================================================
    # DATABASE TRANSACTION
    #
    # Lock ONLY the Student row.
    #
    # IMPORTANT:
    # Do NOT use:
    #
    # .select_related('adviser')
    #
    # together with select_for_update()
    # because adviser is nullable and PostgreSQL
    # may reject FOR UPDATE on the nullable LEFT JOIN.
    # =================================================

    with transaction.atomic():

        # =================================================
        # FIND + LOCK STUDENT
        # =================================================

        try:

            student = (
                Student.objects
                .select_for_update()
                .get(
                    rfid=rfid
                )
            )

        except Student.DoesNotExist:

            return JsonResponse(
                {
                    'success': False,
                    'error': 'RFID card not registered.'
                },
                status=404
            )

        # =================================================
        # GET OR CREATE TODAY'S ATTENDANCE
        # =================================================

        attendance, created = (
            Attendance.objects.get_or_create(
                student=student,
                date=current_date,
            )
        )

        # =================================================
        # CHECK DUPLICATE SCAN
        # =================================================

        existing_value = getattr(
            attendance,
            target_field
        )

        if existing_value:

            duplicate_messages = {

                'time_in_am':
                    (
                        'AM TIME IN is already '
                        'recorded.'
                    ),

                'time_out_am':
                    (
                        'AM TIME OUT is already '
                        'recorded.'
                    ),

                'time_in_pm':
                    (
                        'PM TIME IN is already '
                        'recorded.'
                    ),

                'time_out_pm':
                    (
                        'PM TIME OUT is already '
                        'recorded.'
                    ),
            }

            return JsonResponse(
                {
                    'success': False,

                    'error': duplicate_messages[
                        target_field
                    ],

                    'field': target_field,

                    'label': attendance_label,
                },
                status=400
            )

        # =================================================
        # SAVE ONLY THE CORRECT TIME FIELD
        # =================================================

        setattr(
            attendance,
            target_field,
            current_time
        )

        # =================================================
        # SAVE RFID
        # =================================================

        attendance.rfid_scanned = rfid

        # =================================================
        # UPDATE STATUS
        # =================================================

        if attendance.time_in_am:

            if (
                attendance.time_in_am
                >
                time_cls(8, 0)
            ):

                attendance.status = 'late'

            else:

                attendance.status = 'present'

        else:

            attendance.status = 'present'

        # =================================================
        # SAVE ATTENDANCE
        # =================================================

        attendance.save()

    # =================================================
    # STUDENT PICTURE
    # =================================================

    try:

        if (
            student.image
            and
            student.image.storage.exists(
                student.image.name
            )
        ):

            picture = student.image.url

        else:

            picture = (
                '/static/images/'
                'default-student.png'
            )

    except (
        ValueError,
        OSError
    ):

        picture = (
            '/static/images/'
            'default-student.png'
        )

    # =================================================
    # STUDENT NAME
    # =================================================

    middle = (
        student.middle_name or ''
    ).strip()

    if middle:

        student_name = (
            f"{student.last_name}, "
            f"{student.first_name} "
            f"{middle}"
        )

    else:

        student_name = (
            f"{student.last_name}, "
            f"{student.first_name}"
        )

    # =================================================
    # ADVISER
    # =================================================

    adviser_name = ''

    if student.adviser:

        adviser_name = (
            f"{student.adviser.first_name} "
            f"{student.adviser.last_name}"
        ).strip()

    # =================================================
    # ATTENDANCE TYPE
    # =================================================

    if 'in' in target_field:

        attendance_type = 'IN'

    else:

        attendance_type = 'OUT'

    # =================================================
    # RETURN DATA
    # =================================================

    return JsonResponse({

        'success': True,

        'message': (
            f'{attendance_label} recorded successfully.'
        ),

        'attendance': {

            'date':
                current_date.strftime(
                    '%B %d, %Y'
                ),

            'time':
                current_time.strftime(
                    '%I:%M:%S %p'
                ),

            'field':
                target_field,

            'type':
                attendance_type,

            'label':
                attendance_label,

            'status':
                attendance.status,

        },

        'student': {

            'id':
                student.id,

            'rfid':
                student.rfid or '',

            'lrn':
                student.lrn or '',

            'first_name':
                student.first_name or '',

            'middle_name':
                student.middle_name or '',

            'last_name':
                student.last_name or '',

            'name':
                student_name,

            'department':
                student.department or '',

            'adviser':
                adviser_name,

            'grade':
                student.grade or '',

            'section':
                student.section or '',

            'picture':
                picture,

        }

    })

# =====================================================
# ADMIN — DASHBOARD
# =====================================================

@login_required
def admin_dashboard(request):

    today = date_cls.today()

    admin_dept = get_admin_department(
        request
    )

    teachers_qs = Teacher.objects.all()

    students_qs = Student.objects.filter(
        is_active=True
    )

    classes_qs = Class.objects.all()

    attendance_qs = Attendance.objects.filter(
        date=today
    )

    if admin_dept:

        teachers_qs = teachers_qs.filter(
            department=admin_dept
        )

        students_qs = students_qs.filter(
            department=admin_dept
        )

        classes_qs = classes_qs.filter(
            department=admin_dept
        )

        attendance_qs = attendance_qs.filter(
            student__department=admin_dept
        )

    total_teachers = teachers_qs.count()

    total_students = students_qs.count()

    total_classes = classes_qs.count()

    total_today = attendance_qs.count()

    present_today = attendance_qs.filter(
        status='present'
    ).count()

    attendance_rate = (
        round(
            (
                present_today
                /
                total_today
            ) * 100
        )
        if total_today > 0
        else 0
    )

    recent_attendance = []

    for record in (
        attendance_qs
        .select_related('student')
        .order_by('-created_at')[:4]
    ):

        student = record.student

        recent_attendance.append({

            'initials': (
                (
                    student.first_name[:1]
                    if student.first_name
                    else ''
                )
                +
                (
                    student.last_name[:1]
                    if student.last_name
                    else ''
                )
            ).upper(),

            'full_name':
                student.full_name,

            'student_id':
                student.lrn,

            'time_in': (
                record.time_in_am.strftime(
                    '%I:%M %p'
                )
                if record.time_in_am
                else '—'
            ),

            'status':
                record.get_status_display(),

        })

    context = {

        'total_teachers':
            total_teachers,

        'total_students':
            total_students,

        'total_classes':
            total_classes,

        'attendance_rate':
            attendance_rate,

        'recent_attendance':
            recent_attendance,

        'admin_dept':
            admin_dept,

    }

    return render(
        request,
        'ADMIN/Admin_Dashboard.html',
        context
    )


# =====================================================
# ADMIN — USERS
# =====================================================

@login_required
def admin_users(request):

    admin_dept = get_admin_department(
        request
    )

    teachers = (
        Teacher.objects
        .select_related('user')
        .order_by(
            'last_name',
            'first_name'
        )
    )

    if admin_dept:

        teachers = teachers.filter(
            department=admin_dept
        )

    return render(
        request,
        'ADMIN/Admin_Users.html',
        {
            'teachers': teachers,
            'admin_dept': admin_dept,
        }
    )


# =====================================================
# ADMIN — TEACHERS INFO
# =====================================================

@login_required
def admin_teachers(request):

    admin_dept = get_admin_department(
        request
    )

    teachers = (
        Teacher.objects
        .all()
        .order_by(
            'last_name',
            'first_name'
        )
    )

    if admin_dept:

        teachers = teachers.filter(
            department=admin_dept
        )

    return render(
        request,
        'ADMIN/Admin_Teachers_Info.html',
        {
            'teachers': teachers,
            'admin_dept': admin_dept,
        }
    )


# =====================================================
# ADMIN — DELETE TEACHER
# =====================================================

@login_required
@require_http_methods(["POST"])
def delete_teacher(
    request,
    teacher_id
):

    try:

        teacher = Teacher.objects.get(
            id=teacher_id
        )

    except Teacher.DoesNotExist:

        return JsonResponse(
            {
                'success': False,
                'error': 'Teacher not found'
            },
            status=404
        )

    admin_dept = get_admin_department(
        request
    )

    if (
        admin_dept
        and
        teacher.department != admin_dept
    ):

        return JsonResponse(
            {
                'success': False,
                'error':
                    'Not authorized for this department.'
            },
            status=403
        )

    user = teacher.user

    teacher.delete()

    if user:

        user.delete()

    return JsonResponse({
        'success': True
    })


# =====================================================
# ADMIN — EDIT TEACHER
# =====================================================

@login_required
@csrf_protect
@require_http_methods(["POST"])
def edit_teacher(
    request,
    teacher_id
):

    try:

        teacher = Teacher.objects.get(
            id=teacher_id
        )

    except Teacher.DoesNotExist:

        return JsonResponse(
            {
                'success': False,
                'error': 'Teacher not found'
            },
            status=404
        )

    admin_dept = get_admin_department(
        request
    )

    if (
        admin_dept
        and
        teacher.department != admin_dept
    ):

        return JsonResponse(
            {
                'success': False,
                'error':
                    'Not authorized for this department.'
            },
            status=403
        )

    try:

        payload = json.loads(
            request.body
        )

    except json.JSONDecodeError:

        return JsonResponse(
            {
                'success': False,
                'error': 'Invalid JSON'
            },
            status=400
        )

    teacher.teacher_id = payload.get(
        'teacher_id',
        teacher.teacher_id
    )

    teacher.first_name = payload.get(
        'first_name',
        teacher.first_name
    )

    teacher.last_name = payload.get(
        'last_name',
        teacher.last_name
    )

    teacher.middle_name = payload.get(
        'middle_name',
        teacher.middle_name
    )

    teacher.age = (
        int(payload.get('age') or 0)
        or None
    )

    teacher.sex = payload.get(
        'sex',
        teacher.sex
    )

    teacher.birthday = (
        payload.get('birthday')
        or None
    )

    teacher.email = payload.get(
        'email',
        teacher.email
    )

    teacher.contact = payload.get(
        'contact',
        teacher.contact
    )

    teacher.grade = payload.get(
        'grade',
        teacher.grade
    )

    teacher.section = payload.get(
        'section',
        teacher.section
    )

    if not admin_dept:

        teacher.department = payload.get(
            'department',
            teacher.department
        )

    teacher.save()

    new_grade = payload.get(
        'grade',
        teacher.grade
    )

    new_section = payload.get(
        'section',
        teacher.section
    )

    class_obj = (
        Class.objects
        .filter(teacher=teacher)
        .first()
    )

    if class_obj:

        if new_grade:

            class_obj.grade = new_grade

        if new_section:

            class_obj.section = new_section

        class_obj.save()

    return JsonResponse({
        'success': True
    })


# =====================================================
# ADMIN — STUDENTS INFO
# =====================================================

@login_required
def admin_students(request):

    admin_dept = get_admin_department(
        request
    )

    students = (
        Student.objects
        .select_related('adviser')
        .order_by(
            'last_name',
            'first_name'
        )
    )

    if admin_dept:

        students = students.filter(
            department=admin_dept
        )

    total_students = students.count()

    shs_count = students.filter(
        department='SHS'
    ).count()

    jhs_count = students.filter(
        department='JHS'
    ).count()

    rfid_count = (
        students
        .exclude(rfid__isnull=True)
        .exclude(rfid='')
        .count()
    )

    sections = (
        Student.objects
        .values_list(
            'section',
            flat=True
        )
        .distinct()
        .order_by('section')
    )

    if admin_dept:

        sections = (
            Student.objects
            .filter(
                department=admin_dept
            )
            .values_list(
                'section',
                flat=True
            )
            .distinct()
            .order_by('section')
        )

    context = {

        'students':
            students,

        'total_students':
            total_students,

        'shs_count':
            shs_count,

        'jhs_count':
            jhs_count,

        'rfid_count':
            rfid_count,

        'sections':
            sections,

        'admin_dept':
            admin_dept,

    }

    return render(
        request,
        'ADMIN/Admin_Students_Info.html',
        context
    )


# =====================================================
# ADMIN — EDIT STUDENT
# =====================================================

@login_required
@csrf_protect
@require_http_methods(["POST"])
def edit_student(
    request,
    student_id
):

    try:

        student = Student.objects.get(
            id=student_id
        )

    except Student.DoesNotExist:

        return JsonResponse(
            {
                'success': False,
                'error': 'Student not found'
            },
            status=404
        )

    admin_dept = get_admin_department(
        request
    )

    if (
        admin_dept
        and
        student.department != admin_dept
    ):

        return JsonResponse(
            {
                'success': False,
                'error':
                    'Not authorized for this department.'
            },
            status=403
        )

    try:

        payload = json.loads(
            request.body
        )

    except json.JSONDecodeError:

        return JsonResponse(
            {
                'success': False,
                'error': 'Invalid JSON'
            },
            status=400
        )

    student.lrn = payload.get(
        'lrn',
        student.lrn
    )

    student.rfid = (
        payload.get('rfid')
        or None
    )

    student.first_name = payload.get(
        'first_name',
        student.first_name
    )

    student.last_name = payload.get(
        'last_name',
        student.last_name
    )

    student.middle_name = payload.get(
        'middle_name',
        student.middle_name
    )

    student.age = (
        int(payload.get('age'))
        if payload.get('age')
        else None
    )

    student.sex = payload.get(
        'sex',
        student.sex
    )

    student.email = payload.get(
        'email',
        student.email
    )

    student.contact = payload.get(
        'contact',
        student.contact
    )

    student.barangay = payload.get(
        'barangay',
        student.barangay
    )

    student.municipality = payload.get(
        'municipality',
        student.municipality
    )

    student.province = payload.get(
        'province',
        student.province
    )

    student.grade = payload.get(
        'grade',
        student.grade
    )

    student.section = payload.get(
        'section',
        student.section
    )

    student.parent_name = payload.get(
        'parent_name',
        student.parent_name
    )

    student.parent_relationship = payload.get(
        'parent_relationship',
        student.parent_relationship
    )

    student.parent_contact = payload.get(
        'parent_contact',
        student.parent_contact
    )

    status = payload.get(
        'status',
        'Active'
    )

    student.is_active = (
        str(status)
        .strip()
        .lower()
        ==
        'active'
    )

    if not admin_dept:

        student.department = payload.get(
            'department',
            student.department
        )

    # =================================================
    # AUTOMATIC ADVISER
    # =================================================

    student.adviser = None

    if (
        student.grade
        and
        student.section
    ):

        class_obj = (
            Class.objects
            .filter(
                grade=student.grade,
                section__iexact=student.section,
            )
            .select_related('teacher')
            .first()
        )

        if (
            class_obj
            and
            class_obj.teacher
        ):

            student.adviser = (
                class_obj.teacher
            )

    # =================================================
    # SAVE
    # =================================================

    student.save()

    return JsonResponse({

        'success':
            True,

        'message':
            'Student information updated successfully.'

    })


# =====================================================
# ADMIN — DELETE STUDENT
# =====================================================

@login_required
@csrf_protect
@require_http_methods(["POST"])
def delete_student(
    request,
    student_id
):

    try:

        student = Student.objects.get(
            id=student_id
        )

    except Student.DoesNotExist:

        return JsonResponse(
            {
                'success': False,
                'error': 'Student not found'
            },
            status=404
        )

    admin_dept = get_admin_department(
        request
    )

    if (
        admin_dept
        and
        student.department != admin_dept
    ):

        return JsonResponse(
            {
                'success': False,
                'error':
                    'Not authorized for this department.'
            },
            status=403
        )

    student.delete()

    return JsonResponse({
        'success': True
    })


# =====================================================
# ADMIN — CLASSES
# =====================================================

@login_required
def admin_classes(request):

    admin_dept = get_admin_department(
        request
    )

    classes = (
        Class.objects
        .select_related('teacher')
        .all()
        .order_by(
            'grade',
            'section'
        )
    )

    teachers = (
        Teacher.objects
        .all()
        .order_by(
            'last_name',
            'first_name'
        )
    )

    if admin_dept:

        classes = classes.filter(
            department=admin_dept
        )

        teachers = teachers.filter(
            department=admin_dept
        )

    total_sections = classes.count()

    total_students_qs = Student.objects.filter(
        is_active=True
    )

    if admin_dept:

        total_students_qs = (
            total_students_qs.filter(
                department=admin_dept
            )
        )

    total_students = (
        total_students_qs.count()
    )

    total_teachers = (
        classes
        .exclude(
            teacher__isnull=True
        )
        .values('teacher')
        .distinct()
        .count()
    )

    total_jhs = classes.filter(
        department='JHS'
    ).count()

    total_shs = classes.filter(
        department='SHS'
    ).count()

    # =================================================
    # CLASS DATA
    # =================================================

    classes_data = []

    for class_obj in classes:

        student_count = (
            Student.objects
            .filter(
                grade=class_obj.grade,
                section=class_obj.section,
                department=class_obj.department,
                is_active=True,
            )
            .count()
        )

        classes_data.append({

            'id':
                class_obj.id,

            'grade':
                class_obj.grade.replace(
                    'Grade ',
                    ''
                ).strip(),

            'section':
                class_obj.section,

            'teacher':
                (
                    f"{class_obj.teacher.first_name} "
                    f"{class_obj.teacher.last_name}"
                ).strip()
                if class_obj.teacher
                else '',

            'teacherId':
                class_obj.teacher.id
                if class_obj.teacher
                else '',

            'students':
                student_count,

            'department':
                class_obj.department,

            'assigned':
                class_obj.teacher is not None,

        })

    # =================================================
    # TEACHER DATA
    # =================================================

    teachers_data = []

    for teacher in teachers:

        existing_class = (
            Class.objects
            .filter(
                teacher=teacher
            )
            .first()
        )

        teachers_data.append({

            'id':
                teacher.id,

            'name':
                f"{teacher.last_name}, "
                f"{teacher.first_name}",

            'department':
                teacher.department,

            'assigned':
                existing_class is not None,

            'classId':
                existing_class.id
                if existing_class
                else None,

        })

    context = {

        'classes_json':
            classes_data,

        'teachers_json':
            teachers_data,

        'total_sections':
            total_sections,

        'total_students':
            total_students,

        'total_teachers':
            total_teachers,

        'total_jhs':
            total_jhs,

        'total_shs':
            total_shs,

        'teachers':
            teachers,

        'admin_dept':
            admin_dept,

    }

    return render(
        request,
        'ADMIN/Admin_Classes.html',
        context
    )


# =====================================================
# ADMIN — ADD SECTION
# =====================================================

@login_required
@csrf_protect
@require_http_methods(["POST"])
def add_class(request):

    try:

        payload = json.loads(
            request.body
        )

    except json.JSONDecodeError:

        return JsonResponse(
            {
                'success': False,
                'error': 'Invalid JSON.'
            },
            status=400
        )

    admin_dept = get_admin_department(
        request
    )

    grade = (
        payload
        .get('grade', '')
        .strip()
    )

    section = (
        payload
        .get('section', '')
        .strip()
    )

    if not grade or not section:

        return JsonResponse(
            {
                'success': False,
                'error':
                    'Grade and Section Name are required.'
            },
            status=400
        )

    try:

        grade_num = int(
            grade
            .replace(
                'Grade ',
                ''
            )
            .strip()
        )

    except ValueError:

        return JsonResponse(
            {
                'success': False,
                'error':
                    'Invalid grade.'
            },
            status=400
        )

    if grade_num not in (
        7,
        8,
        9,
        10,
        11,
        12
    ):

        return JsonResponse(
            {
                'success': False,
                'error':
                    'Grade must be from Grade 7 to Grade 12.'
            },
            status=400
        )

    if grade_num in (
        7,
        8,
        9,
        10
    ):

        department = 'JHS'

    else:

        department = 'SHS'

    if (
        admin_dept
        and
        department != admin_dept
    ):

        return JsonResponse(
            {
                'success': False,
                'error':
                    f'You can only manage '
                    f'{admin_dept} sections.'
            },
            status=403
        )

    duplicate = (
        Class.objects
        .filter(
            grade=grade,
            section__iexact=section
        )
        .exists()
    )

    if duplicate:

        return JsonResponse(
            {
                'success': False,
                'error':
                    f'Section "{section}" '
                    f'already exists in {grade}.'
            },
            status=400
        )

    class_obj = Class.objects.create(

        department=department,

        grade=grade,

        section=section,

        teacher=None,

    )

    return JsonResponse({

        'success':
            True,

        'message':
            'Section added successfully.',

        'class': {

            'id':
                class_obj.id,

            'grade':
                str(grade_num),

            'section':
                class_obj.section,

            'teacher':
                '',

            'teacherId':
                '',

            'students':
                0,

            'department':
                class_obj.department,

            'assigned':
                False,

        }

    })


# =====================================================
# ADMIN — ASSIGN CLASS
# =====================================================

@login_required
@csrf_protect
@require_http_methods(["POST"])
def assign_class(
    request,
    class_id
):

    try:

        class_obj = (
            Class.objects
            .select_related('teacher')
            .get(
                id=class_id
            )
        )

    except Class.DoesNotExist:

        return JsonResponse(
            {
                'success': False,
                'error':
                    'Section not found.'
            },
            status=404
        )

    admin_dept = get_admin_department(
        request
    )

    if (
        admin_dept
        and
        class_obj.department != admin_dept
    ):

        return JsonResponse(
            {
                'success': False,
                'error':
                    'Not authorized for this department.'
            },
            status=403
        )

    if class_obj.teacher:

        return JsonResponse(
            {
                'success': False,
                'error':
                    'This section already has an adviser.'
            },
            status=400
        )

    try:

        payload = json.loads(
            request.body
        )

    except json.JSONDecodeError:

        return JsonResponse(
            {
                'success': False,
                'error':
                    'Invalid JSON.'
            },
            status=400
        )

    teacher_id = payload.get(
        'teacherId'
    )

    if not teacher_id:

        return JsonResponse(
            {
                'success': False,
                'error':
                    'Please select a teacher.'
            },
            status=400
        )

    try:

        teacher = Teacher.objects.get(
            id=teacher_id
        )

    except Teacher.DoesNotExist:

        return JsonResponse(
            {
                'success': False,
                'error':
                    'Teacher not found.'
            },
            status=404
        )

    try:

        grade_num = int(
            class_obj.grade
            .replace(
                'Grade ',
                ''
            )
            .strip()
        )

    except ValueError:

        return JsonResponse(
            {
                'success': False,
                'error':
                    'Invalid section grade.'
            },
            status=400
        )

    required_department = (
        'JHS'
        if grade_num in (
            7,
            8,
            9,
            10
        )
        else
        'SHS'
    )

    if (
        teacher.department
        !=
        required_department
    ):

        return JsonResponse(
            {
                'success': False,
                'error':
                    (
                        f'{class_obj.grade} requires '
                        f'a {required_department} teacher.'
                    )
            },
            status=400
        )

    if (
        admin_dept
        and
        teacher.department != admin_dept
    ):

        return JsonResponse(
            {
                'success': False,
                'error':
                    'You can only assign teachers '
                    'from your department.'
            },
            status=403
        )

    existing_class = (
        Class.objects
        .filter(
            teacher=teacher
        )
        .first()
    )

    if existing_class:

        return JsonResponse(
            {
                'success': False,
                'error':
                    (
                        f'Teacher '
                        f'{teacher.first_name} '
                        f'{teacher.last_name} '
                        f'is already assigned to '
                        f'{existing_class.grade} - '
                        f'{existing_class.section}.'
                    )
            },
            status=400
        )

    class_obj.teacher = teacher

    class_obj.save(
        update_fields=[
            'teacher',
            'updated_at'
        ]
    )

    teacher.grade = (
        class_obj.grade
    )

    teacher.section = (
        class_obj.section
    )

    teacher.department = (
        class_obj.department
    )

    teacher.save()

    Student.objects.filter(

        grade=class_obj.grade,

        section__iexact=class_obj.section,

        department=class_obj.department,

    ).update(
        adviser=teacher
    )

    return JsonResponse({

        'success':
            True,

        'message':
            'Class assigned successfully.',

        'class': {

            'id':
                class_obj.id,

            'teacher':
                (
                    f"{teacher.first_name} "
                    f"{teacher.last_name}"
                ).strip(),

            'teacherId':
                teacher.id,

            'assigned':
                True,

        }

    })


# =====================================================
# ADMIN — EDIT SECTION NAME
# =====================================================

@login_required
@csrf_protect
@require_http_methods(["POST"])
def edit_class(
    request,
    class_id
):

    try:

        class_obj = (
            Class.objects
            .select_related('teacher')
            .get(
                id=class_id
            )
        )

    except Class.DoesNotExist:

        return JsonResponse(
            {
                'success': False,
                'error':
                    'Section not found.'
            },
            status=404
        )

    admin_dept = get_admin_department(
        request
    )

    if (
        admin_dept
        and
        class_obj.department != admin_dept
    ):

        return JsonResponse(
            {
                'success': False,
                'error':
                    'Not authorized for this department.'
            },
            status=403
        )

    try:

        payload = json.loads(
            request.body
        )

    except json.JSONDecodeError:

        return JsonResponse(
            {
                'success': False,
                'error':
                    'Invalid JSON.'
            },
            status=400
        )

    new_section = (
        payload
        .get(
            'section',
            ''
        )
        .strip()
    )

    if not new_section:

        return JsonResponse(
            {
                'success': False,
                'error':
                    'Section Name is required.'
            },
            status=400
        )

    duplicate = (
        Class.objects
        .filter(
            grade=class_obj.grade,
            section__iexact=new_section
        )
        .exclude(
            id=class_obj.id
        )
        .exists()
    )

    if duplicate:

        return JsonResponse(
            {
                'success': False,
                'error':
                    (
                        f'Section "{new_section}" '
                        f'already exists in '
                        f'{class_obj.grade}.'
                    )
            },
            status=400
        )

    old_section = (
        class_obj.section
    )

    if (
        old_section.strip().lower()
        ==
        new_section.strip().lower()
    ):

        return JsonResponse({

            'success':
                True,

            'message':
                'No changes were made.',

            'class': {

                'id':
                    class_obj.id,

                'section':
                    class_obj.section,

            }

        })

    Student.objects.filter(

        grade=class_obj.grade,

        section__iexact=old_section,

        department=class_obj.department,

    ).update(
        section=new_section
    )

    class_obj.section = (
        new_section
    )

    class_obj.save()

    if class_obj.teacher:

        class_obj.teacher.section = (
            new_section
        )

        class_obj.teacher.save(
            update_fields=[
                'section',
                'updated_at'
            ]
        )

    return JsonResponse({

        'success':
            True,

        'message':
            'Section name updated successfully.',

        'class': {

            'id':
                class_obj.id,

            'section':
                class_obj.section,

        }

    })


# =====================================================
# ADMIN — UNASSIGN CLASS
# =====================================================

@login_required
@csrf_protect
@require_http_methods(["POST"])
def unassign_class(
    request,
    class_id
):

    try:

        class_obj = (
            Class.objects
            .select_related('teacher')
            .get(
                id=class_id
            )
        )

    except Class.DoesNotExist:

        return JsonResponse(
            {
                'success': False,
                'error':
                    'Section not found.'
            },
            status=404
        )

    admin_dept = get_admin_department(
        request
    )

    if (
        admin_dept
        and
        class_obj.department != admin_dept
    ):

        return JsonResponse(
            {
                'success': False,
                'error':
                    'Not authorized for this department.'
            },
            status=403
        )

    if not class_obj.teacher:

        return JsonResponse(
            {
                'success': False,
                'error':
                    'This section has no assigned adviser.'
            },
            status=400
        )

    teacher = class_obj.teacher

    Student.objects.filter(

        grade=class_obj.grade,

        section__iexact=class_obj.section,

        department=class_obj.department,

        adviser=teacher,

    ).update(
        adviser=None
    )

    teacher.grade = None

    teacher.section = None

    teacher.save(
        update_fields=[
            'grade',
            'section',
            'updated_at'
        ]
    )

    class_obj.teacher = None

    class_obj.save(
        update_fields=[
            'teacher',
            'updated_at'
        ]
    )

    return JsonResponse({

        'success':
            True,

        'message':
            'Teacher unassigned successfully.',

        'class': {

            'id':
                class_obj.id,

            'teacher':
                '',

            'teacherId':
                '',

            'assigned':
                False,

        }

    })


# =====================================================
# ADMIN — DELETE SECTION
# =====================================================

@login_required
@csrf_protect
@require_http_methods(["POST"])
def delete_class(
    request,
    class_id
):

    try:

        class_obj = (
            Class.objects
            .select_related('teacher')
            .get(
                id=class_id
            )
        )

    except Class.DoesNotExist:

        return JsonResponse(
            {
                'success': False,
                'error':
                    'Section not found.'
            },
            status=404
        )

    admin_dept = get_admin_department(
        request
    )

    if (
        admin_dept
        and
        class_obj.department != admin_dept
    ):

        return JsonResponse(
            {
                'success': False,
                'error':
                    'Not authorized for this department.'
            },
            status=403
        )

    student_count = (
        Student.objects
        .filter(

            grade=class_obj.grade,

            section__iexact=class_obj.section,

            department=class_obj.department,

        )
        .count()
    )

    if student_count > 0:

        return JsonResponse(
            {
                'success': False,
                'error':
                    (
                        f'Cannot delete this section because '
                        f'it still contains {student_count} '
                        f'student(s).'
                    )
            },
            status=400
        )

    if class_obj.teacher:

        teacher = class_obj.teacher

        teacher.grade = None

        teacher.section = None

        teacher.save(
            update_fields=[
                'grade',
                'section',
                'updated_at'
            ]
        )

    class_obj.delete()

    return JsonResponse({

        'success':
            True,

        'message':
            'Section deleted successfully.'

    })


# =====================================================
# ADMIN — ADD CLASS
# =====================================================

@login_required
@csrf_protect
@require_http_methods(["POST"])
def add_class(request):

    try:

        payload = json.loads(
            request.body
        )

    except json.JSONDecodeError:

        return JsonResponse(
            {
                'success': False,
                'error': 'Invalid JSON'
            },
            status=400
        )

    admin_dept = get_admin_department(
        request
    )

    grade = (
        payload
        .get(
            'grade',
            ''
        )
        .strip()
    )

    section = (
        payload
        .get(
            'section',
            ''
        )
        .strip()
    )

    teacher_id = payload.get(
        'teacherId'
    )

    if not grade or not section:

        return JsonResponse(
            {
                'success': False,
                'error':
                    'Grade and Section are required.'
            },
            status=400
        )

    try:

        grade_num = int(
            grade
            .replace(
                'Grade ',
                ''
            )
            .strip()
        )

        department = (
            'SHS'
            if grade_num >= 11
            else
            'JHS'
        )

    except ValueError:

        return JsonResponse(
            {
                'success': False,
                'error':
                    'Invalid grade.'
            },
            status=400
        )

    if (
        admin_dept
        and
        department != admin_dept
    ):

        if admin_dept == 'SHS':

            return JsonResponse({
                'success':
                    False,

                'error':
                    'SHS admin can only add Grade 11 and 12 classes.'
            }, status=403)

        else:

            return JsonResponse({
                'success':
                    False,

                'error':
                    'JHS admin can only add Grade 7-10 classes.'
            }, status=403)

    if (
        Class.objects
        .filter(
            grade=grade,
            section__iexact=section
        )
        .exists()
    ):

        return JsonResponse({

            'success':
                False,

            'error':
                f'Section "{section}" '
                f'in {grade} already exists.'

        }, status=400)

    teacher = None

    if teacher_id:

        try:

            teacher = Teacher.objects.get(
                id=teacher_id
            )

        except Teacher.DoesNotExist:

            return JsonResponse(
                {
                    'success': False,
                    'error':
                        'Teacher not found'
                },
                status=404
            )

        if (
            admin_dept
            and
            teacher.department != admin_dept
        ):

            return JsonResponse({

                'success':
                    False,

                'error':
                    'You can only assign teachers in your department.'

            }, status=403)

        existing_class = (
            Class.objects
            .filter(
                teacher=teacher
            )
            .first()
        )

        if existing_class:

            return JsonResponse({

                'success':
                    False,

                'error':
                    (
                        f'Teacher '
                        f'{teacher.first_name} '
                        f'{teacher.last_name} '
                        f'already has '
                        f'a class: '
                        f'{existing_class.grade} - '
                        f'{existing_class.section}.'
                    )

            }, status=400)

    class_obj = Class.objects.create(

        department=department,

        teacher=teacher,

        grade=grade,

        section=section,

    )

    if teacher:

        teacher.grade = grade

        teacher.section = section

        teacher.department = department

        teacher.save()

    return JsonResponse({

        'success':
            True,

        'class': {

            'id':
                class_obj.id,

            'grade':
                class_obj.grade.replace(
                    'Grade ',
                    ''
                ).strip(),

            'section':
                class_obj.section,

            'teacher':
                (
                    f"{teacher.first_name} "
                    f"{teacher.last_name}".strip()
                    if teacher
                    else ''
                ),

            'teacherId':
                teacher.id
                if teacher
                else '',

            'department':
                class_obj.department,

            'students':
                0,

        }

    })


# =====================================================
# ADMIN — EDIT CLASS
# =====================================================

@login_required
@csrf_protect
@require_http_methods(["POST"])
def edit_class(
    request,
    class_id
):

    try:

        class_obj = Class.objects.get(
            id=class_id
        )

    except Class.DoesNotExist:

        return JsonResponse(
            {
                'success': False,
                'error':
                    'Class not found'
            },
            status=404
        )

    admin_dept = get_admin_department(
        request
    )

    if (
        admin_dept
        and
        class_obj.department != admin_dept
    ):

        return JsonResponse({
            'success': False,
            'error':
                'Not authorized for this department.'
        }, status=403)

    try:

        payload = json.loads(
            request.body
        )

    except json.JSONDecodeError:

        return JsonResponse({
            'success': False,
            'error':
                'Invalid JSON'
        }, status=400)

    new_grade = (
        payload
        .get(
            'grade',
            class_obj.grade
        )
        .strip()
    )

    new_section = (
        payload
        .get(
            'section',
            class_obj.section
        )
        .strip()
    )

    new_teacher_id = payload.get(
        'teacherId'
    )

    try:

        grade_num = int(
            new_grade
            .replace(
                'Grade ',
                ''
            )
            .strip()
        )

        new_department = (
            'SHS'
            if grade_num >= 11
            else
            'JHS'
        )

    except ValueError:

        new_department = (
            class_obj.department
        )

    if (
        admin_dept
        and
        new_department != admin_dept
    ):

        return JsonResponse({

            'success':
                False,

            'error':
                f'You can only manage '
                f'{admin_dept} classes.'

        }, status=403)

    if (
        Class.objects
        .filter(
            grade=new_grade,
            section__iexact=new_section
        )
        .exclude(
            id=class_id
        )
        .exists()
    ):

        return JsonResponse({

            'success':
                False,

            'error':
                (
                    f'Section "{new_section}" '
                    f'in {new_grade} already exists.'
                )

        }, status=400)

    class_obj.grade = new_grade

    class_obj.section = new_section

    class_obj.department = new_department

    if new_teacher_id:

        try:

            new_teacher = Teacher.objects.get(
                id=new_teacher_id
            )

        except Teacher.DoesNotExist:

            return JsonResponse(
                {
                    'success': False,
                    'error':
                        'Teacher not found'
                },
                status=404
            )

        if (
            admin_dept
            and
            new_teacher.department != admin_dept
        ):

            return JsonResponse({

                'success':
                    False,

                'error':
                    'You can only assign teachers in your department.'

            }, status=403)

        existing = (
            Class.objects
            .filter(
                teacher=new_teacher
            )
            .exclude(
                id=class_id
            )
            .first()
        )

        if existing:

            return JsonResponse({

                'success':
                    False,

                'error':
                    (
                        f'Teacher '
                        f'{new_teacher.first_name} '
                        f'{new_teacher.last_name} '
                        f'already has '
                        f'a class: '
                        f'{existing.grade} - '
                        f'{existing.section}.'
                    )

            }, status=400)

        class_obj.teacher = (
            new_teacher
        )

    class_obj.save()

    if class_obj.teacher:

        class_obj.teacher.grade = (
            class_obj.grade
        )

        class_obj.teacher.section = (
            class_obj.section
        )

        class_obj.teacher.department = (
            class_obj.department
        )

        class_obj.teacher.save()

    return JsonResponse({
        'success': True
    })


# =====================================================
# ADMIN — DELETE CLASS
# =====================================================

@login_required
@csrf_protect
@require_http_methods(["POST"])
def delete_class(
    request,
    class_id
):

    try:

        class_obj = Class.objects.get(
            id=class_id
        )

    except Class.DoesNotExist:

        return JsonResponse(
            {
                'success': False,
                'error':
                    'Class not found'
            },
            status=404
        )

    admin_dept = get_admin_department(
        request
    )

    if (
        admin_dept
        and
        class_obj.department != admin_dept
    ):

        return JsonResponse({

            'success':
                False,

            'error':
                'Not authorized for this department.'

        }, status=403)

    if class_obj.teacher:

        teacher = (
            class_obj.teacher
        )

        teacher.grade = None

        teacher.section = None

        teacher.save()

    class_obj.delete()

    return JsonResponse({
        'success': True
    })


# =====================================================
# ADMIN — STUDENT ATTENDANCE
# =====================================================

@login_required
def admin_attendance(request):

    admin_dept = get_admin_department(
        request
    )

    today = (
        date_cls.today()
        .isoformat()
    )

    students = (
        Student.objects
        .filter(
            is_active=True
        )
        .order_by(
            'last_name',
            'first_name'
        )
    )

    if admin_dept:

        students = students.filter(
            department=admin_dept
        )

    students_data = [

        {

            'id':
                s.id,

            'name':
                s.full_name,

            'grade':
                str(
                    s.grade
                )
                .replace(
                    'Grade ',
                    ''
                )
                .strip(),

            'section':
                s.section or '',

        }

        for s in students
    ]

    context = {

        'today':
            today,

        'students_json':
            students_data,

        'admin_dept':
            admin_dept,

    }

    return render(
        request,
        'ADMIN/Admin_Student_Attendance.html',
        context
    )


# =====================================================
# ADMIN — REGISTER RFID STUDENT
# =====================================================

@login_required
def admin_register_rfid(request):

    admin_dept = get_admin_department(
        request
    )

    if request.method == 'POST':

        rfid = request.POST.get(
            'rfid',
            ''
        ).strip()

        lrn = request.POST.get(
            'lrn',
            ''
        ).strip()

        first_name = request.POST.get(
            'firstName',
            ''
        ).strip()

        last_name = request.POST.get(
            'lastName',
            ''
        ).strip()

        middle_name = request.POST.get(
            'middleName',
            ''
        ).strip()

        age = request.POST.get(
            'age'
        ) or None

        sex = request.POST.get(
            'sex',
            ''
        ).strip()

        email = request.POST.get(
            'email',
            ''
        ).strip()

        contact = request.POST.get(
            'contact',
            ''
        ).strip()

        barangay = request.POST.get(
            'barangay',
            ''
        ).strip()

        municipality = request.POST.get(
            'municipality',
            ''
        ).strip()

        province = request.POST.get(
            'province',
            ''
        ).strip()

        guardian_last = request.POST.get(
            'guardianLastName',
            ''
        ).strip()

        guardian_first = request.POST.get(
            'guardianFirstName',
            ''
        ).strip()

        relationship = request.POST.get(
            'relationship',
            ''
        ).strip()

        guardian_contact = request.POST.get(
            'guardianContact',
            ''
        ).strip()

        guardian_first = (
            " ".join(
                guardian_first.split()
            )
        )

        guardian_last = (
            " ".join(
                guardian_last.split()
            )
        )

        department = (
            request.POST.get(
                'department',
                ''
            )
            .strip()
            .upper()
        )

        grade = request.POST.get(
            'grade',
            ''
        ).strip()

        section = request.POST.get(
            'section',
            ''
        ).strip()

        adviser_name = request.POST.get(
            'adviser',
            ''
        ).strip()

        image = request.FILES.get(
            'studentImage'
        )

        if (
            admin_dept
            and
            department != admin_dept
        ):

            messages.error(
                request,
                f'You can only register '
                f'{admin_dept} students.'
            )

            return redirect(
                'admin_register_rfid'
            )

        try:

            grade_num = int(
                grade
                .replace(
                    'Grade ',
                    ''
                )
                .strip()
            )

        except (
            ValueError,
            AttributeError
        ):

            grade_num = 0

        if (
            admin_dept == 'SHS'
            and
            grade_num not in (
                11,
                12
            )
        ):

            messages.error(
                request,
                'SHS admin can only register Grade 11 or 12 students.'
            )

            return redirect(
                'admin_register_rfid'
            )

        if (
            admin_dept == 'JHS'
            and
            grade_num not in (
                7,
                8,
                9,
                10
            )
        ):

            messages.error(
                request,
                'JHS admin can only register Grade 7-10 students.'
            )

            return redirect(
                'admin_register_rfid'
            )

        if (
            rfid
            and
            Student.objects
            .filter(
                rfid=rfid
            )
            .exists()
        ):

            messages.error(
                request,
                'RFID card is already registered.'
            )

            return redirect(
                'admin_register_rfid'
            )

        if (
            Student.objects
            .filter(
                lrn=lrn
            )
            .exists()
        ):

            messages.error(
                request,
                'LRN already exists.'
            )

            return redirect(
                'admin_register_rfid'
            )

        adviser = None

        if grade and section:

            class_obj = (
                Class.objects
                .filter(
                    grade=grade,
                    section__iexact=section,
                )
                .select_related('teacher')
                .first()
            )

            if (
                class_obj
                and
                class_obj.teacher
            ):

                adviser = (
                    class_obj.teacher
                )

        if (
            not adviser
            and
            adviser_name
        ):

            adviser = (
                Teacher.objects
                .filter(
                    Q(
                        first_name__icontains=
                        adviser_name
                    )
                    |
                    Q(
                        last_name__icontains=
                        adviser_name
                    )
                )
                .first()
            )

        parent_name = (
            f"{guardian_first} "
            f"{guardian_last}"
        ).strip()

        parent_name = (
            " ".join(
                parent_name.split()
            )
        )

        Student.objects.create(

            lrn=lrn,

            first_name=first_name,

            last_name=last_name,

            middle_name=middle_name or '',

            age=int(age) if age else 0,

            sex=sex or '',

            email=email or '',

            contact=contact or '',

            parent_name=parent_name,

            parent_contact=guardian_contact,

            parent_relationship=relationship,

            barangay=barangay,

            municipality=municipality,

            province=province,

            department=department,

            grade=grade,

            section=section,

            adviser=adviser,

            rfid=rfid or None,

            image=image,
        )

        messages.success(
            request,
            'Student registered successfully!'
        )

        return redirect(
            'admin_students'
        )

    classes = (
        Class.objects
        .select_related('teacher')
        .all()
    )

    if admin_dept:

        classes = classes.filter(
            department=admin_dept
        )

    classes_data = [

        {

            'id':
                c.id,

            'grade':
                c.grade,

            'section':
                c.section,

            'teacher':
                (
                    f"{c.teacher.first_name} "
                    f"{c.teacher.last_name}"
                ).strip()
                if c.teacher
                else "",

            'department':
                c.department,

        }

        for c in classes
    ]

    return render(
        request,
        'ADMIN/Admin_Register_RFID.html',
        {
            'classes_json':
                classes_data,

            'admin_dept':
                admin_dept,
        }
    )


# =====================================================
# ADMIN — ADD TEACHER
# =====================================================

@login_required
def admin_add_teacher(request):

    admin_dept = get_admin_department(
        request
    )

    return render(
        request,
        'ADMIN/Admin_Add_Teacher.html',
        {
            'admin_dept':
                admin_dept,
        }
    )


# =====================================================
# ADMIN — ATTENDANCE AJAX
# =====================================================

@login_required
@csrf_protect
@require_http_methods(["GET", "POST"])
def save_attendance(request):

    admin_dept = get_admin_department(
        request
    )

    if request.method == 'GET':

        date_str = (
            request.GET.get('date')
            or
            date_cls.today().isoformat()
        )

        records = Attendance.objects.filter(
            date=date_str
        )

        if admin_dept:

            records = records.filter(
                student__department=admin_dept
            )

        data = [

            {

                'student_id':
                    r.student_id,

                'timeInAM':
                    (
                        r.time_in_am.strftime(
                            '%H:%M'
                        )
                        if r.time_in_am
                        else ''
                    ),

                'timeOutAM':
                    (
                        r.time_out_am.strftime(
                            '%H:%M'
                        )
                        if r.time_out_am
                        else ''
                    ),

                'timeInPM':
                    (
                        r.time_in_pm.strftime(
                            '%H:%M'
                        )
                        if r.time_in_pm
                        else ''
                    ),

                'timeOutPM':
                    (
                        r.time_out_pm.strftime(
                            '%H:%M'
                        )
                        if r.time_out_pm
                        else ''
                    ),

                'status':
                    r.status,

            }

            for r in records
        ]

        return JsonResponse({
            'success':
                True,
            'records':
                data
        })

    try:

        payload = json.loads(
            request.body
        )

    except json.JSONDecodeError:

        return JsonResponse({
            'success':
                False,
            'error':
                'Invalid JSON'
        }, status=400)

    student_id = payload.get(
        'student_id'
    )

    field = payload.get(
        'field'
    )

    value = payload.get(
        'value',
        ''
    )

    date_str = (
        payload.get('date')
        or
        date_cls.today().isoformat()
    )

    try:

        student = Student.objects.get(
            id=student_id
        )

    except Student.DoesNotExist:

        return JsonResponse({
            'success':
                False,
            'error':
                'Student not found'
        }, status=404)

    if (
        admin_dept
        and
        student.department != admin_dept
    ):

        return JsonResponse({
            'success':
                False,
            'error':
                'Not authorized'
        }, status=403)

    field_map = {

        'timeInAM':
            'time_in_am',

        'timeOutAM':
            'time_out_am',

        'timeInPM':
            'time_in_pm',

        'timeOutPM':
            'time_out_pm',

    }

    if field not in field_map:

        return JsonResponse({
            'success':
                False,
            'error':
                'Invalid field'
        }, status=400)

    record, _ = (
        Attendance.objects
        .get_or_create(
            student_id=student_id,
            date=date_str,
        )
    )

    setattr(
        record,
        field_map[field],
        value or None
    )

    if any([
        record.time_in_am,
        record.time_out_am,
        record.time_in_pm,
        record.time_out_pm
    ]):

        if (
            record.time_in_am
            and
            record.time_in_am
            >
            time_cls(8, 0)
        ):

            record.status = 'late'

        else:

            record.status = 'present'

    else:

        record.status = 'absent'

    record.save()

    return JsonResponse({
        'success':
            True
    })


# =====================================================
# ADMIN — BULK ATTENDANCE
# =====================================================

@login_required
@csrf_protect
@require_http_methods(["POST"])
def bulk_attendance(request):

    admin_dept = get_admin_department(
        request
    )

    try:

        payload = json.loads(
            request.body
        )

    except json.JSONDecodeError:

        return JsonResponse({
            'success':
                False,
            'error':
                'Invalid JSON'
        }, status=400)

    action = payload.get(
        'action'
    )

    date_str = (
        payload.get('date')
        or
        date_cls.today().isoformat()
    )

    student_ids = payload.get(
        'student_ids',
        []
    )

    if action not in (
        'present',
        'absent',
        'clear'
    ):

        return JsonResponse({
            'success':
                False,
            'error':
                'Invalid action'
        }, status=400)

    for sid in student_ids:

        try:

            student = Student.objects.get(
                id=sid
            )

        except Student.DoesNotExist:

            continue

        if (
            admin_dept
            and
            student.department != admin_dept
        ):

            continue

        record, _ = (
            Attendance.objects
            .get_or_create(
                student_id=sid,
                date=date_str,
            )
        )

        if action == 'present':

            record.time_in_am = (
                time_cls(7, 30)
            )

            record.time_out_am = (
                time_cls(11, 30)
            )

            record.time_in_pm = (
                time_cls(12, 30)
            )

            record.time_out_pm = (
                time_cls(16, 30)
            )

            record.status = 'present'

        else:

            record.time_in_am = None

            record.time_out_am = None

            record.time_in_pm = None

            record.time_out_pm = None

            record.status = 'absent'

        record.save()

    return JsonResponse({

        'success':
            True,

        'updated':
            len(student_ids)

    })


# =====================================================
# ADMIN — RESET ATTENDANCE
# =====================================================

@login_required
@csrf_protect
@require_http_methods(["POST"])
def reset_attendance(request):

    admin_dept = get_admin_department(
        request
    )

    try:

        payload = json.loads(
            request.body
        )

    except json.JSONDecodeError:

        return JsonResponse({
            'success':
                False,
            'error':
                'Invalid JSON'
        }, status=400)

    date_str = (
        payload.get('date')
        or
        date_cls.today().isoformat()
    )

    qs = Attendance.objects.filter(
        date=date_str
    )

    if admin_dept:

        qs = qs.filter(
            student__department=admin_dept
        )

    qs.delete()

    return JsonResponse({
        'success':
            True
    })


# =====================================================
# TEACHER — DASHBOARD
# =====================================================

@login_required
def teacher_dashboard(request):

    today = date_cls.today()

    teacher = get_teacher(
        request
    )

    students_qs = Student.objects.filter(
        is_active=True
    )

    if (
        teacher
        and
        teacher.grade
        and
        teacher.section
    ):

        students_qs = students_qs.filter(

            grade=teacher.grade,

            section=teacher.section,

        )

    total_students = (
        students_qs.count()
    )

    student_ids = list(
        students_qs.values_list(
            'id',
            flat=True
        )
    )

    today_records = (
        Attendance.objects
        .filter(
            date=today,
            student_id__in=student_ids,
        )
    )

    total_present = (
        today_records
        .filter(
            status='present'
        )
        .count()
    )

    total_absent = (
        today_records
        .filter(
            status='absent'
        )
        .count()
    )

    if total_students > 0:

        attendance_rate = round(
            (
                total_present
                /
                total_students
            ) * 100
        )

    else:

        attendance_rate = 0

    recent_attendance = (
        Attendance.objects
        .filter(
            student_id__in=student_ids,
        )
        .select_related(
            'student'
        )
        .order_by(
            '-date',
            '-time_in_am'
        )[:10]
    )

    notifications = (
        Notification.objects
        .filter(
            user=request.user
        )
        .order_by(
            '-created_at'
        )[:20]
    )

    context = {

        'teacher':
            teacher,

        'teacher_name':
            (
                teacher.full_name
                if teacher
                else request.user.username
            ),

        'teacher_initials':
            (
                teacher.initials
                if teacher
                else 'T'
            ),

        'total_students':
            total_students,

        'total_present':
            total_present,

        'total_absent':
            total_absent,

        'attendance_rate':
            attendance_rate,

        'recent_attendance':
            recent_attendance,

        'notifications':
            notifications,

    }

    return render(
        request,
        'TEACHER/Teacher_Dashboard.html',
        context
    )


# =====================================================
# TEACHER — CLASS ATTENDANCE
# =====================================================

@login_required
def teacher_class_attendance(request):

    teacher = get_teacher(
        request
    )

    selected_date_str = request.GET.get(
        'date'
    )

    if selected_date_str:

        try:

            selected_date = (
                date_cls.fromisoformat(
                    selected_date_str
                )
            )

        except ValueError:

            selected_date = (
                date_cls.today()
            )

    else:

        selected_date = (
            date_cls.today()
        )

    students_qs = Student.objects.filter(
        is_active=True
    )

    if (
        teacher
        and
        teacher.grade
        and
        teacher.section
    ):

        students_qs = students_qs.filter(

            grade=teacher.grade,

            section=teacher.section,

        )

    student_ids = list(
        students_qs.values_list(
            'id',
            flat=True
        )
    )

    records = (
        Attendance.objects
        .filter(
            date=selected_date,
            student_id__in=student_ids,
        )
        .select_related(
            'student'
        )
        .order_by(
            'student__last_name'
        )
    )

    total_students = (
        students_qs.count()
    )

    total_present = (
        records
        .filter(
            status='present'
        )
        .count()
    )

    total_absent = (
        records
        .filter(
            status='absent'
        )
        .count()
    )

    if (
        teacher
        and
        teacher.grade
        and
        teacher.section
    ):

        section_name = (
            f"{teacher.grade} - "
            f"{teacher.section}"
        )

    else:

        section_name = (
            "Not Assigned"
        )

    dates_with_records = list(
        Attendance.objects
        .filter(
            student_id__in=student_ids,
        )
        .values_list(
            'date',
            flat=True
        )
        .distinct()
    )

    dates_with_records_str = [
        d.isoformat()
        for d in dates_with_records
    ]

    context = {

        'selected_date':
            selected_date,

        'records':
            records,

        'total_students':
            total_students,

        'total_present':
            total_present,

        'total_absent':
            total_absent,

        'section_name':
            section_name,

        'dates_with_records':
            dates_with_records_str,

    }

    return render(
        request,
        'TEACHER/Teacher_Class_Attendance.html',
        context
    )


# =====================================================
# TEACHER — CLASS RECORD
# =====================================================

@login_required
def teacher_class_record(request):

    teacher = get_teacher(
        request
    )

    grade = (
        teacher.grade
        if teacher
        and teacher.grade
        else None
    )

    section = (
        teacher.section
        if teacher
        and teacher.section
        else None
    )

    if grade and section:

        students = (
            Student.objects
            .filter(
                is_active=True,
                grade=grade,
                section=section,
            )
            .order_by(
                'last_name',
                'first_name'
            )
        )

    else:

        students = (
            Student.objects.none()
        )

    grade_options = [

        "Grade 7",
        "Grade 8",
        "Grade 9",
        "Grade 10",
        "Grade 11",
        "Grade 12"

    ]

    section_options = [

        "Section A",
        "Section B",
        "Section C",
        "Section D"

    ]

    context = {

        'students':
            students,

        'grade':
            grade or "Not Assigned",

        'section':
            section or "",

        'grade_options':
            grade_options,

        'section_options':
            section_options,

    }

    return render(
        request,
        'TEACHER/Teacher_Class_Record.html',
        context
    )


# =====================================================
# TEACHER — PROFILE / PERSONAL INFO
# =====================================================

@login_required
def teacher_profile(request):

    teacher = get_teacher(
        request
    )

    if (
        request.method == 'POST'
        and
        teacher
    ):

        teacher.first_name = request.POST.get(
            'first_name',
            teacher.first_name
        )

        teacher.last_name = request.POST.get(
            'last_name',
            teacher.last_name
        )

        teacher.middle_name = request.POST.get(
            'middle_name',
            teacher.middle_name
        )

        teacher.age = (
            request.POST.get(
                'age'
            )
            or None
        )

        teacher.sex = request.POST.get(
            'sex',
            teacher.sex
        )

        teacher.birthday = (
            request.POST.get(
                'birthday'
            )
            or None
        )

        teacher.email = request.POST.get(
            'email',
            teacher.email
        )

        teacher.contact = request.POST.get(
            'contact',
            teacher.contact
        )

        teacher.department = request.POST.get(
            'department',
            teacher.department
        )

        teacher.save()

        messages.success(
            request,
            "Personal information updated successfully!"
        )

        return redirect(
            'teacher_profile'
        )

    context = {

        'teacher':
            teacher,

    }

    return render(
        request,
        'TEACHER/Teacher_Personal_Info.html',
        context
    )


# =====================================================
# TEACHER — HISTORY
# =====================================================

@login_required
def teacher_history(request):

    teacher = get_teacher(
        request
    )

    students_qs = Student.objects.filter(
        is_active=True
    )

    if (
        teacher
        and
        teacher.grade
        and
        teacher.section
    ):

        students_qs = students_qs.filter(

            grade=teacher.grade,

            section=teacher.section,

        )

    students = (
        students_qs
        .order_by(
            'last_name',
            'first_name'
        )
    )

    student_names = [
        s.full_name
        for s in students
    ]

    student_ids = list(
        students.values_list(
            'id',
            flat=True
        )
    )

    records = (
        Attendance.objects
        .filter(
            student_id__in=student_ids,
        )
        .select_related(
            'student'
        )
        .order_by(
            '-date'
        )
    )

    records_by_date = {}

    for record in records:

        date_key = (
            record.date.isoformat()
        )

        if date_key not in records_by_date:

            records_by_date[
                date_key
            ] = {}

        records_by_date[
            date_key
        ][
            record.student.id
        ] = record

    history_records = []

    for date_key in sorted(
        records_by_date.keys(),
        reverse=True
    ):

        daily = (
            records_by_date[
                date_key
            ]
        )

        attendance = []

        for student in students:

            record = daily.get(
                student.id
            )

            if record:

                attendance.append([

                    (
                        record.time_in_am.strftime(
                            "%#I:%M %p"
                        )
                        if record.time_in_am
                        else "—"
                    ),

                    (
                        record.time_out_am.strftime(
                            "%#I:%M %p"
                        )
                        if record.time_out_am
                        else "—"
                    ),

                    (
                        record.time_in_pm.strftime(
                            "%#I:%M %p"
                        )
                        if record.time_in_pm
                        else "—"
                    ),

                    (
                        record.time_out_pm.strftime(
                            "%#I:%M %p"
                        )
                        if record.time_out_pm
                        else "—"
                    ),

                ])

            else:

                attendance.append(
                    None
                )

        history_records.append({

            'date':
                date_key,

            'attendance':
                attendance,

        })

    context = {

        'student_names':
            student_names,

        'history_records':
            history_records,

    }

    return render(
        request,
        'TEACHER/Teacher_History.html',
        context
    )


# =====================================================
# TEACHER — SECURITY
# =====================================================

@login_required
def teacher_security(request):

    teacher = get_teacher(
        request
    )

    context = {

        'security':
            teacher,

    }

    return render(
        request,
        'TEACHER/Teacher_Security.html',
        context
    )


# =====================================================
# TEACHER — CHANGE PASSWORD
# =====================================================

@login_required
def teacher_change_password(request):

    if request.method == 'POST':

        current_password = request.POST.get(
            'current_password'
        )

        new_password = request.POST.get(
            'new_password'
        )

        confirm_password = request.POST.get(
            'confirm_password'
        )

        if not request.user.check_password(
            current_password
        ):

            messages.error(
                request,
                "Current password is incorrect."
            )

            return redirect(
                'teacher_security'
            )

        if (
            new_password
            !=
            confirm_password
        ):

            messages.error(
                request,
                "New passwords do not match."
            )

            return redirect(
                'teacher_security'
            )

        if len(new_password) < 8:

            messages.error(
                request,
                "Password must be at least 8 characters."
            )

            return redirect(
                'teacher_security'
            )

        request.user.set_password(
            new_password
        )

        request.user.save()

        update_session_auth_hash(
            request,
            request.user
        )

        messages.success(
            request,
            "Password changed successfully!"
        )

        return redirect(
            'teacher_security'
        )

    return redirect(
        'teacher_security'
    )


# =====================================================
# TEACHER — SAVE SECURITY
# =====================================================

@login_required
def teacher_save_security(request):

    if request.method == 'POST':

        try:

            teacher = (
                request.user.teacher_profile
            )

            teacher.security_question = (
                request.POST.get(
                    'security_question',
                    ''
                )
            )

            teacher.security_answer = (
                make_password(
                    request.POST.get(
                        'security_answer',
                        ''
                    )
                )
            )

            teacher.plain_security_answer = (
                request.POST.get(
                    'security_answer',
                    ''
                )
            )

            teacher.save()

            messages.success(
                request,
                "Security settings saved successfully!"
            )

        except Teacher.DoesNotExist:

            messages.error(
                request,
                "Teacher profile not found."
            )

        return redirect(
            'teacher_security'
        )

    return redirect(
        'teacher_security'
    )


# =====================================================
# TEACHER — ATTENDANCE EXCEL EXPORT
# =====================================================

def get_teacher_attendance_records(
    request,
    start_date,
    end_date
):
    """
    Get attendance records only for the
    currently logged-in teacher's assigned class.
    """

    teacher = get_teacher(request)

    if not teacher:
        return None, Attendance.objects.none()

    students_qs = Student.objects.filter(
        is_active=True
    )

    if (
        teacher.grade
        and teacher.section
    ):

        students_qs = students_qs.filter(
            grade=teacher.grade,
            section=teacher.section,
        )

    else:

        return teacher, Attendance.objects.none()

    student_ids = students_qs.values_list(
        'id',
        flat=True
    )

    records = (
        Attendance.objects
        .filter(
            student_id__in=student_ids,
            date__range=(
                start_date,
                end_date
            ),
        )
        .select_related('student')
        .order_by(
            'date',
            'student__last_name',
            'student__first_name'
        )
    )

    return teacher, records


def create_attendance_excel(
    records,
    report_title,
    start_date,
    end_date
):
    """
    Create Excel workbook for attendance records.
    """

    workbook = Workbook()

    worksheet = workbook.active
    worksheet.title = "Attendance"

    # =================================================
    # TITLE
    # =================================================

    worksheet.merge_cells(
        'A1:I1'
    )

    worksheet['A1'] = report_title

    worksheet['A1'].font = Font(
        bold=True,
        size=14
    )

    worksheet['A1'].alignment = Alignment(
        horizontal='center',
        vertical='center'
    )

    worksheet.row_dimensions[1].height = 25

    # =================================================
    # DATE RANGE
    # =================================================

    worksheet.merge_cells(
        'A2:I2'
    )

    if start_date == end_date:

        date_text = (
            start_date.strftime(
                '%B %d, %Y'
            )
        )

    else:

        date_text = (
            f"{start_date.strftime('%B %d, %Y')} "
            f"to "
            f"{end_date.strftime('%B %d, %Y')}"
        )

    worksheet['A2'] = date_text

    worksheet['A2'].alignment = Alignment(
        horizontal='center'
    )

    # =================================================
    # HEADER
    # =================================================

    headers = [

        'Date',
        'LRN',
        'Student Name',
        'Section',
        'AM Time In',
        'AM Time Out',
        'PM Time In',
        'PM Time Out',
        'Status',

    ]

    header_row = 4

    for column, header in enumerate(
        headers,
        start=1
    ):

        cell = worksheet.cell(
            row=header_row,
            column=column
        )

        cell.value = header

        cell.font = Font(
            bold=True
        )

        cell.alignment = Alignment(
            horizontal='center',
            vertical='center'
        )

        cell.fill = PatternFill(
            fill_type='solid',
            fgColor='E9ECEF'
        )

    # =================================================
    # DATA
    # =================================================

    row = 5

    for record in records:

        student = record.student

        worksheet.cell(
            row=row,
            column=1
        ).value = record.date.strftime(
            '%B %d, %Y'
        )

        worksheet.cell(
            row=row,
            column=2
        ).value = student.lrn

        worksheet.cell(
            row=row,
            column=3
        ).value = student.full_name

        worksheet.cell(
            row=row,
            column=4
        ).value = student.section

        worksheet.cell(
            row=row,
            column=5
        ).value = (
            record.time_in_am.strftime(
                '%I:%M %p'
            )
            if record.time_in_am
            else ''
        )

        worksheet.cell(
            row=row,
            column=6
        ).value = (
            record.time_out_am.strftime(
                '%I:%M %p'
            )
            if record.time_out_am
            else ''
        )

        worksheet.cell(
            row=row,
            column=7
        ).value = (
            record.time_in_pm.strftime(
                '%I:%M %p'
            )
            if record.time_in_pm
            else ''
        )

        worksheet.cell(
            row=row,
            column=8
        ).value = (
            record.time_out_pm.strftime(
                '%I:%M %p'
            )
            if record.time_out_pm
            else ''
        )

        worksheet.cell(
            row=row,
            column=9
        ).value = record.get_status_display()

        row += 1

    # =================================================
    # BORDERS & ALIGNMENT
    # =================================================

    thin_border = Border(
        left=Side(
            style='thin',
            color='D9D9D9'
        ),
        right=Side(
            style='thin',
            color='D9D9D9'
        ),
        top=Side(
            style='thin',
            color='D9D9D9'
        ),
        bottom=Side(
            style='thin',
            color='D9D9D9'
        )
    )

    for row_cells in worksheet.iter_rows(
        min_row=header_row,
        max_row=max(row - 1, header_row),
        min_col=1,
        max_col=9
    ):

        for cell in row_cells:

            cell.border = thin_border

            cell.alignment = Alignment(
                vertical='center'
            )

    # =================================================
    # COLUMN WIDTHS
    # =================================================

    widths = {

        'A': 18,
        'B': 18,
        'C': 30,
        'D': 18,
        'E': 16,
        'F': 16,
        'G': 16,
        'H': 16,
        'I': 14,

    }

    for column, width in widths.items():

        worksheet.column_dimensions[
            column
        ].width = width

    # =================================================
    # FREEZE HEADER
    # =================================================

    worksheet.freeze_panes = 'A5'

    # =================================================
    # RESPONSE
    # =================================================

    response = HttpResponse(
        content_type=(
            'application/vnd.openxmlformats-officedocument'
            '.spreadsheetml.sheet'
        )
    )

    response[
        'Content-Disposition'
    ] = (
        f'attachment; filename="{report_title}.xlsx"'
    )

    workbook.save(response)

    return response


# =====================================================
# TEACHER — DAILY EXCEL REPORT
# =====================================================

@login_required
def export_attendance_daily(request):

    selected_date_str = request.GET.get(
        'date'
    )

    if selected_date_str:

        try:

            selected_date = (
                date_cls.fromisoformat(
                    selected_date_str
                )
            )

        except ValueError:

            selected_date = date_cls.today()

    else:

        selected_date = date_cls.today()

    teacher, records = (
        get_teacher_attendance_records(
            request,
            selected_date,
            selected_date
        )
    )

    if not teacher:

        return HttpResponse(
            'Teacher profile not found.',
            status=403
        )

    report_title = (
        'Daily Attendance Report'
    )

    return create_attendance_excel(
        records,
        report_title,
        selected_date,
        selected_date
    )


# =====================================================
# TEACHER — WEEKLY EXCEL REPORT
# =====================================================

@login_required
def export_attendance_weekly(request):

    selected_date_str = request.GET.get(
        'date'
    )

    if selected_date_str:

        try:

            selected_date = (
                date_cls.fromisoformat(
                    selected_date_str
                )
            )

        except ValueError:

            selected_date = date_cls.today()

    else:

        selected_date = date_cls.today()

    # Monday = start of week
    start_date = (
        selected_date
        -
        timedelta(
            days=selected_date.weekday()
        )
    )

    # Sunday = end of week
    end_date = (
        start_date
        +
        timedelta(days=6)
    )

    teacher, records = (
        get_teacher_attendance_records(
            request,
            start_date,
            end_date
        )
    )

    if not teacher:

        return HttpResponse(
            'Teacher profile not found.',
            status=403
        )

    report_title = (
        'Weekly Attendance Report'
    )

    return create_attendance_excel(
        records,
        report_title,
        start_date,
        end_date
    )


# =====================================================
# TEACHER — MONTHLY EXCEL REPORT
# =====================================================

@login_required
def export_attendance_monthly(request):

    selected_date_str = request.GET.get(
        'date'
    )

    if selected_date_str:

        try:

            selected_date = (
                date_cls.fromisoformat(
                    selected_date_str
                )
            )

        except ValueError:

            selected_date = date_cls.today()

    else:

        selected_date = date_cls.today()

    # First day of month
    start_date = selected_date.replace(
        day=1
    )

    # First day of next month
    if selected_date.month == 12:

        next_month = selected_date.replace(
            year=selected_date.year + 1,
            month=1,
            day=1
        )

    else:

        next_month = selected_date.replace(
            month=selected_date.month + 1,
            day=1
        )

    # Last day of current month
    end_date = (
        next_month
        -
        timedelta(days=1)
    )

    teacher, records = (
        get_teacher_attendance_records(
            request,
            start_date,
            end_date
        )
    )

    if not teacher:

        return HttpResponse(
            'Teacher profile not found.',
            status=403
        )

    report_title = (
        'Monthly Attendance Report'
    )

    return create_attendance_excel(
        records,
        report_title,
        start_date,
        end_date
    )
