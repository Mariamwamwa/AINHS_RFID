import json
from datetime import date as date_cls, time as time_cls

from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.db.models import Q

from .models import Admin, Teacher, Student, Class, Attendance


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

        user = authenticate(request, username=username, password=password)

        if user is not None:

            if role == 'admin':
                if user.is_superuser or user.is_staff:
                    login(request, user)
                    return redirect('admin_dashboard')
                messages.error(request, 'You are not authorized as admin.')
                return redirect('login')

            elif role == 'teacher':
                try:
                    Teacher.objects.get(user=user)
                    login(request, user)
                    return redirect('teacher_dashboard')
                except Teacher.DoesNotExist:
                    messages.error(request, 'No teacher profile found.')
                    return redirect('login')

            else:
                messages.error(request, 'Please select an account type.')
                return redirect('login')

        else:
            messages.error(request, 'Invalid username or password.')
            return render(request, 'AUTHENTICATION/Login_Page.html')

    return render(request, 'AUTHENTICATION/Login_Page.html')


def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('login')


def register_page(request):
    if request.method == 'POST':

        id_number = request.POST.get('id_number', '').strip()
        role = (request.POST.get('role') or '').upper()
        department = request.POST.get('department', '').strip().upper()
        last_name = request.POST.get('last_name', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        middle_name = request.POST.get('middle_name', '').strip()
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        security_question = request.POST.get('security_question', '')
        security_answer = request.POST.get('security_answer', '').strip()

        age = request.POST.get('age') or None
        sex = request.POST.get('sex', '')
        birthday = request.POST.get('birthday') or None
        email = request.POST.get('email', '')
        contact = request.POST.get('contact', '')

        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'AUTHENTICATION/Register_Page.html')

        if department not in ('JHS', 'SHS'):
            messages.error(request, 'Please select a valid department.')
            return render(request, 'AUTHENTICATION/Register_Page.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return render(request, 'AUTHENTICATION/Register_Page.html')

        if role == 'TEACHER' and Teacher.objects.filter(teacher_id=id_number).exists():
            messages.error(request, 'Teacher ID already exists.')
            return render(request, 'AUTHENTICATION/Register_Page.html')

        if role == 'ADMIN' and Admin.objects.filter(admin_id=id_number).exists():
            messages.error(request, 'Admin ID already exists.')
            return render(request, 'AUTHENTICATION/Register_Page.html')

        # =================================================
        # CREATE USER
        # Admin → is_staff=True, is_superuser=False
        # Teacher → is_staff=False, is_superuser=False
        # =================================================
        if role == 'ADMIN':
            user = User.objects.create_user(
                username=username, password=password,
                first_name=first_name, last_name=last_name,
                email=email or '',
                is_staff=True, is_superuser=False,
            )
        else:
            user = User.objects.create_user(
                username=username, password=password,
                first_name=first_name, last_name=last_name,
                email=email or '',
                is_staff=False, is_superuser=False,
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
                security_answer=make_password(security_answer),
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
                security_answer=make_password(security_answer),
                plain_password=password,
                plain_security_answer=security_answer,
            )

        messages.success(request, 'Account created successfully!')
        return redirect('login')

    return render(request, 'AUTHENTICATION/Register_Page.html')


def attendance_page(request):
    return render(request, 'AUTHENTICATION/Attendance_Page.html')


# =====================================================
# ADMIN — DASHBOARD
# =====================================================

@login_required
def admin_dashboard(request):
    today = date_cls.today()
    admin_dept = get_admin_department(request)

    teachers_qs = Teacher.objects.all()
    students_qs = Student.objects.filter(is_active=True)
    classes_qs = Class.objects.all()
    attendance_qs = Attendance.objects.filter(date=today)

    if admin_dept:
        teachers_qs = teachers_qs.filter(department=admin_dept)
        students_qs = students_qs.filter(department=admin_dept)
        classes_qs = classes_qs.filter(department=admin_dept)
        attendance_qs = attendance_qs.filter(student__department=admin_dept)

    total_teachers = teachers_qs.count()
    total_students = students_qs.count()
    total_classes = classes_qs.count()

    total_today = attendance_qs.count()
    present_today = attendance_qs.filter(status='present').count()

    attendance_rate = (
        round((present_today / total_today) * 100)
        if total_today > 0 else 0
    )

    recent_attendance = []
    for record in attendance_qs.select_related('student').order_by('-created_at')[:4]:
        student = record.student
        recent_attendance.append({
            'initials': (
                (student.first_name[:1] if student.first_name else '') +
                (student.last_name[:1] if student.last_name else '')
            ).upper(),
            'full_name': student.full_name,
            'student_id': student.lrn,
            'time_in': (
                record.time_in_am.strftime('%I:%M %p')
                if record.time_in_am else '—'
            ),
            'status': record.get_status_display(),
        })

    context = {
        'total_teachers': total_teachers,
        'total_students': total_students,
        'total_classes': total_classes,
        'attendance_rate': attendance_rate,
        'recent_attendance': recent_attendance,
        'admin_dept': admin_dept,
    }
    return render(request, 'ADMIN/Admin_Dashboard.html', context)


# =====================================================
# ADMIN — USERS
# =====================================================

@login_required
def admin_users(request):
    admin_dept = get_admin_department(request)

    teachers = Teacher.objects.select_related('user').order_by('last_name', 'first_name')
    if admin_dept:
        teachers = teachers.filter(department=admin_dept)

    return render(request, 'ADMIN/Admin_Users.html', {
        'teachers': teachers,
        'admin_dept': admin_dept,
    })


# =====================================================
# ADMIN — TEACHERS INFO
# =====================================================

@login_required
def admin_teachers(request):
    admin_dept = get_admin_department(request)

    teachers = Teacher.objects.all().order_by('last_name', 'first_name')
    if admin_dept:
        teachers = teachers.filter(department=admin_dept)

    return render(request, 'ADMIN/Admin_Teachers_Info.html', {
        'teachers': teachers,
        'admin_dept': admin_dept,
    })


# =====================================================
# ADMIN — DELETE TEACHER
# =====================================================

@login_required
@require_http_methods(["POST"])
def delete_teacher(request, teacher_id):
    try:
        teacher = Teacher.objects.get(id=teacher_id)
    except Teacher.DoesNotExist:
        return JsonResponse(
            {'success': False, 'error': 'Teacher not found'},
            status=404
        )

    admin_dept = get_admin_department(request)
    if admin_dept and teacher.department != admin_dept:
        return JsonResponse(
            {'success': False, 'error': 'Not authorized for this department.'},
            status=403
        )

    user = teacher.user
    teacher.delete()
    if user:
        user.delete()

    return JsonResponse({'success': True})


# =====================================================
# ADMIN — EDIT TEACHER
# =====================================================

@login_required
@csrf_protect
@require_http_methods(["POST"])
def edit_teacher(request, teacher_id):
    try:
        teacher = Teacher.objects.get(id=teacher_id)
    except Teacher.DoesNotExist:
        return JsonResponse(
            {'success': False, 'error': 'Teacher not found'},
            status=404
        )

    admin_dept = get_admin_department(request)
    if admin_dept and teacher.department != admin_dept:
        return JsonResponse(
            {'success': False, 'error': 'Not authorized for this department.'},
            status=403
        )

    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse(
            {'success': False, 'error': 'Invalid JSON'},
            status=400
        )

    teacher.teacher_id  = payload.get('teacher_id', teacher.teacher_id)
    teacher.first_name  = payload.get('first_name', teacher.first_name)
    teacher.last_name   = payload.get('last_name', teacher.last_name)
    teacher.middle_name = payload.get('middle_name', teacher.middle_name)
    teacher.age         = int(payload.get('age') or 0) or None
    teacher.sex         = payload.get('sex', teacher.sex)
    teacher.birthday    = payload.get('birthday') or None
    teacher.email       = payload.get('email', teacher.email)
    teacher.contact     = payload.get('contact', teacher.contact)
    teacher.grade       = payload.get('grade', teacher.grade)
    teacher.section     = payload.get('section', teacher.section)

    if not admin_dept:
        teacher.department = payload.get('department', teacher.department)

    teacher.save()

    new_grade      = payload.get('grade', teacher.grade)
    new_section    = payload.get('section', teacher.section)

    class_obj = Class.objects.filter(teacher=teacher).first()
    if class_obj:
        if new_grade:
            class_obj.grade = new_grade
        if new_section:
            class_obj.section = new_section
        class_obj.save()

    return JsonResponse({'success': True})


# =====================================================
# ADMIN — STUDENTS INFO
# =====================================================

@login_required
def admin_students(request):
    admin_dept = get_admin_department(request)

    students = Student.objects.select_related('adviser').order_by('last_name', 'first_name')
    if admin_dept:
        students = students.filter(department=admin_dept)

    total_students = students.count()
    shs_count = students.filter(department='SHS').count()
    jhs_count = students.filter(department='JHS').count()
    rfid_count = students.exclude(rfid__isnull=True).exclude(rfid='').count()

    sections = (
        Student.objects.values_list('section', flat=True)
        .distinct().order_by('section')
    )

    if admin_dept:
        sections = (
            Student.objects.filter(department=admin_dept)
            .values_list('section', flat=True)
            .distinct().order_by('section')
        )

    context = {
        'students': students,
        'total_students': total_students,
        'shs_count': shs_count,
        'jhs_count': jhs_count,
        'rfid_count': rfid_count,
        'sections': sections,
        'admin_dept': admin_dept,
    }
    return render(request, 'ADMIN/Admin_Students_Info.html', context)


# =====================================================
# ADMIN — EDIT STUDENT
# =====================================================

@login_required
@csrf_protect
@require_http_methods(["POST"])
def edit_student(request, student_id):
    try:
        student = Student.objects.get(id=student_id)
    except Student.DoesNotExist:
        return JsonResponse(
            {'success': False, 'error': 'Student not found'},
            status=404
        )

    admin_dept = get_admin_department(request)
    if admin_dept and student.department != admin_dept:
        return JsonResponse(
            {'success': False, 'error': 'Not authorized for this department.'},
            status=403
        )

    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse(
            {'success': False, 'error': 'Invalid JSON'},
            status=400
        )

    student.lrn          = payload.get('lrn', student.lrn)
    student.rfid         = payload.get('rfid') or None
    student.first_name   = payload.get('first_name', student.first_name)
    student.last_name    = payload.get('last_name', student.last_name)
    student.middle_name  = payload.get('middle_name', student.middle_name)
    student.age          = int(payload.get('age') or 0)
    student.sex          = payload.get('sex', student.sex)
    student.email        = payload.get('email', student.email)
    student.contact      = payload.get('contact', student.contact)
    student.barangay     = payload.get('barangay', student.barangay)
    student.municipality = payload.get('municipality', student.municipality)
    student.province     = payload.get('province', student.province)
    student.grade        = payload.get('grade', student.grade)
    student.section      = payload.get('section', student.section)
    student.parent_name  = payload.get('parent_name', student.parent_name)
    student.parent_relationship = payload.get('parent_relationship', student.parent_relationship)
    student.parent_contact      = payload.get('parent_contact', student.parent_contact)

    if not admin_dept:
        student.department = payload.get('department', student.department)

    if student.grade and student.section:
        class_obj = Class.objects.filter(
            grade=student.grade,
            section__iexact=student.section,
        ).select_related('teacher').first()

        if class_obj and class_obj.teacher:
            student.adviser = class_obj.teacher

    student.save()
    return JsonResponse({'success': True})


# =====================================================
# ADMIN — DELETE STUDENT
# =====================================================

@login_required
@csrf_protect
@require_http_methods(["POST"])
def delete_student(request, student_id):
    try:
        student = Student.objects.get(id=student_id)
    except Student.DoesNotExist:
        return JsonResponse(
            {'success': False, 'error': 'Student not found'},
            status=404
        )

    admin_dept = get_admin_department(request)
    if admin_dept and student.department != admin_dept:
        return JsonResponse(
            {'success': False, 'error': 'Not authorized for this department.'},
            status=403
        )

    student.delete()
    return JsonResponse({'success': True})


# =====================================================
# ADMIN — CLASSES
# =====================================================

@login_required
def admin_classes(request):
    admin_dept = get_admin_department(request)

    classes = Class.objects.select_related('teacher').all()
    teachers = Teacher.objects.all().order_by('last_name', 'first_name')

    if admin_dept:
        classes = classes.filter(department=admin_dept)
        teachers = teachers.filter(department=admin_dept)

    total_sections = classes.count()

    total_students = Student.objects.filter(is_active=True)
    if admin_dept:
        total_students = total_students.filter(department=admin_dept)
    total_students = total_students.count()

    total_teachers = classes.exclude(teacher__isnull=True).values('teacher').distinct().count()
    total_jhs = classes.filter(department='JHS').count()
    total_shs = classes.filter(department='SHS').count()

    classes_data = [
        {
            'id': c.id,
            'grade': c.grade.replace('Grade ', '').strip(),
            'section': c.section,
            'teacher': (
                f"{c.teacher.first_name} {c.teacher.last_name}".strip()
                if c.teacher else ''
            ),
            'teacherId': c.teacher.id if c.teacher else '',
            'students': Student.objects.filter(
                grade=c.grade, section=c.section, department=c.department
            ).count(),
            'department': c.department,
        }
        for c in classes
    ]

    teachers_data = [
        {'id': t.id, 'name': f"{t.last_name}, {t.first_name}"}
        for t in teachers
    ]

    context = {
        'classes_json': classes_data,
        'teachers_json': teachers_data,
        'total_sections': total_sections,
        'total_students': total_students,
        'total_teachers': total_teachers,
        'total_jhs': total_jhs,
        'total_shs': total_shs,
        'teachers': teachers,
        'admin_dept': admin_dept,
    }
    return render(request, 'ADMIN/Admin_Classes.html', context)


# =====================================================
# ADMIN — ADD CLASS
# =====================================================

@login_required
@csrf_protect
@require_http_methods(["POST"])
def add_class(request):
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)

    admin_dept = get_admin_department(request)

    grade = payload.get('grade', '').strip()
    section = payload.get('section', '').strip()
    teacher_id = payload.get('teacherId')

    if not grade or not section:
        return JsonResponse(
            {'success': False, 'error': 'Grade and Section are required.'},
            status=400
        )

    try:
        grade_num = int(grade.replace('Grade ', '').strip())
        department = 'SHS' if grade_num >= 11 else 'JHS'
    except ValueError:
        return JsonResponse(
            {'success': False, 'error': 'Invalid grade.'},
            status=400
        )

    # Enforce department
    if admin_dept and department != admin_dept:
        if admin_dept == 'SHS':
            return JsonResponse({
                'success': False,
                'error': 'SHS admin can only add Grade 11 and 12 classes.'
            }, status=403)
        else:
            return JsonResponse({
                'success': False,
                'error': 'JHS admin can only add Grade 7-10 classes.'
            }, status=403)

    if Class.objects.filter(grade=grade, section__iexact=section).exists():
        return JsonResponse({
            'success': False,
            'error': f'Section "{section}" in {grade} already exists.'
        }, status=400)

    teacher = None
    if teacher_id:
        try:
            teacher = Teacher.objects.get(id=teacher_id)
        except Teacher.DoesNotExist:
            return JsonResponse(
                {'success': False, 'error': 'Teacher not found'},
                status=404
            )

        if admin_dept and teacher.department != admin_dept:
            return JsonResponse({
                'success': False,
                'error': 'You can only assign teachers in your department.'
            }, status=403)

        existing_class = Class.objects.filter(teacher=teacher).first()
        if existing_class:
            return JsonResponse({
                'success': False,
                'error': (
                    f'Teacher {teacher.first_name} {teacher.last_name} already has '
                    f'a class: {existing_class.grade} - {existing_class.section}.'
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
        'success': True,
        'class': {
            'id': class_obj.id,
            'grade': class_obj.grade.replace('Grade ', '').strip(),
            'section': class_obj.section,
            'teacher': (
                f"{teacher.first_name} {teacher.last_name}".strip()
                if teacher else ''
            ),
            'teacherId': teacher.id if teacher else '',
            'department': class_obj.department,
            'students': 0,
        }
    })


# =====================================================
# ADMIN — EDIT CLASS
# =====================================================

@login_required
@csrf_protect
@require_http_methods(["POST"])
def edit_class(request, class_id):
    try:
        class_obj = Class.objects.get(id=class_id)
    except Class.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Class not found'}, status=404)

    admin_dept = get_admin_department(request)
    if admin_dept and class_obj.department != admin_dept:
        return JsonResponse({
            'success': False,
            'error': 'Not authorized for this department.'
        }, status=403)

    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)

    new_grade = payload.get('grade', class_obj.grade).strip()
    new_section = payload.get('section', class_obj.section).strip()
    new_teacher_id = payload.get('teacherId')

    try:
        grade_num = int(new_grade.replace('Grade ', '').strip())
        new_department = 'SHS' if grade_num >= 11 else 'JHS'
    except ValueError:
        new_department = class_obj.department

    if admin_dept and new_department != admin_dept:
        return JsonResponse({
            'success': False,
            'error': f'You can only manage {admin_dept} classes.'
        }, status=403)

    if Class.objects.filter(
        grade=new_grade, section__iexact=new_section
    ).exclude(id=class_id).exists():
        return JsonResponse({
            'success': False,
            'error': f'Section "{new_section}" in {new_grade} already exists.'
        }, status=400)

    class_obj.grade = new_grade
    class_obj.section = new_section
    class_obj.department = new_department

    if new_teacher_id:
        try:
            new_teacher = Teacher.objects.get(id=new_teacher_id)
        except Teacher.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Teacher not found'}, status=404)

        if admin_dept and new_teacher.department != admin_dept:
            return JsonResponse({
                'success': False,
                'error': 'You can only assign teachers in your department.'
            }, status=403)

        existing = Class.objects.filter(teacher=new_teacher).exclude(id=class_id).first()
        if existing:
            return JsonResponse({
                'success': False,
                'error': (
                    f'Teacher {new_teacher.first_name} {new_teacher.last_name} already has '
                    f'a class: {existing.grade} - {existing.section}.'
                )
            }, status=400)

        class_obj.teacher = new_teacher

    class_obj.save()

    if class_obj.teacher:
        class_obj.teacher.grade = class_obj.grade
        class_obj.teacher.section = class_obj.section
        class_obj.teacher.department = class_obj.department
        class_obj.teacher.save()

    return JsonResponse({'success': True})


# =====================================================
# ADMIN — DELETE CLASS
# =====================================================

@login_required
@csrf_protect
@require_http_methods(["POST"])
def delete_class(request, class_id):
    try:
        class_obj = Class.objects.get(id=class_id)
    except Class.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Class not found'}, status=404)

    admin_dept = get_admin_department(request)
    if admin_dept and class_obj.department != admin_dept:
        return JsonResponse({
            'success': False,
            'error': 'Not authorized for this department.'
        }, status=403)

    if class_obj.teacher:
        teacher = class_obj.teacher
        teacher.grade = None
        teacher.section = None
        teacher.save()

    class_obj.delete()
    return JsonResponse({'success': True})


# =====================================================
# ADMIN — STUDENT ATTENDANCE
# =====================================================

@login_required
def admin_attendance(request):
    admin_dept = get_admin_department(request)
    today = date_cls.today().isoformat()

    students = Student.objects.filter(is_active=True).order_by('last_name', 'first_name')
    if admin_dept:
        students = students.filter(department=admin_dept)

    students_data = [
        {
            'id': s.id,
            'name': s.full_name,
            'grade': str(s.grade).replace('Grade ', '').strip(),
            'section': s.section or '',
        }
        for s in students
    ]

    context = {
        'today': today,
        'students_json': students_data,
        'admin_dept': admin_dept,
    }
    return render(request, 'ADMIN/Admin_Student_Attendance.html', context)


# =====================================================
# ADMIN — REGISTER RFID (STUDENT)
# =====================================================

@login_required
def admin_register_rfid(request):

    admin_dept = get_admin_department(request)

    if request.method == 'POST':
        rfid = request.POST.get('rfid', '').strip()
        lrn = request.POST.get('lrn', '').strip()
        first_name = request.POST.get('firstName', '').strip()
        last_name = request.POST.get('lastName', '').strip()
        middle_name = request.POST.get('middleName', '').strip()
        age = request.POST.get('age') or None
        sex = request.POST.get('sex', '').strip()
        email = request.POST.get('email', '').strip()
        contact = request.POST.get('contact', '').strip()
        barangay = request.POST.get('barangay', '').strip()
        municipality = request.POST.get('municipality', '').strip()
        province = request.POST.get('province', '').strip()

        guardian_last = request.POST.get('guardianLastName', '').strip()
        guardian_first = request.POST.get('guardianFirstName', '').strip()
        relationship = request.POST.get('relationship', '').strip()
        guardian_contact = request.POST.get('guardianContact', '').strip()

        guardian_first = " ".join(guardian_first.split())
        guardian_last = " ".join(guardian_last.split())

        department = request.POST.get('department', '').strip().upper()
        grade = request.POST.get('grade', '').strip()
        section = request.POST.get('section', '').strip()
        adviser_name = request.POST.get('adviser', '').strip()

        image = request.FILES.get('studentImage')

        # Enforce department
        if admin_dept and department != admin_dept:
            messages.error(request, f'You can only register {admin_dept} students.')
            return redirect('admin_register_rfid')

        # Enforce grade range
        try:
            grade_num = int(grade.replace('Grade ', '').strip())
        except (ValueError, AttributeError):
            grade_num = 0

        if admin_dept == 'SHS' and grade_num not in (11, 12):
            messages.error(request, 'SHS admin can only register Grade 11 or 12 students.')
            return redirect('admin_register_rfid')

        if admin_dept == 'JHS' and grade_num not in (7, 8, 9, 10):
            messages.error(request, 'JHS admin can only register Grade 7-10 students.')
            return redirect('admin_register_rfid')

        if rfid and Student.objects.filter(rfid=rfid).exists():
            messages.error(request, 'RFID card is already registered.')
            return redirect('admin_register_rfid')

        if Student.objects.filter(lrn=lrn).exists():
            messages.error(request, 'LRN already exists.')
            return redirect('admin_register_rfid')

        adviser = None
        if grade and section:
            class_obj = Class.objects.filter(
                grade=grade,
                section__iexact=section,
            ).select_related('teacher').first()

            if class_obj and class_obj.teacher:
                adviser = class_obj.teacher

        if not adviser and adviser_name:
            adviser = Teacher.objects.filter(
                Q(first_name__icontains=adviser_name) |
                Q(last_name__icontains=adviser_name)
            ).first()

        parent_name = f"{guardian_first} {guardian_last}".strip()
        parent_name = " ".join(parent_name.split())

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

        messages.success(request, 'Student registered successfully!')
        return redirect('admin_students')

    # GET — i-load ang classes (filtered by department)
    classes = Class.objects.select_related('teacher').all()
    if admin_dept:
        classes = classes.filter(department=admin_dept)

    classes_data = [
        {
            'id': c.id,
            'grade': c.grade,
            'section': c.section,
            'teacher': (
                f"{c.teacher.first_name} {c.teacher.last_name}".strip()
                if c.teacher else ""
            ),
            'department': c.department,
        }
        for c in classes
    ]

    return render(request, 'ADMIN/Admin_Register_RFID.html', {
        'classes_json': classes_data,
        'admin_dept': admin_dept,
    })


# =====================================================
# ADMIN — ADD TEACHER
# =====================================================

@login_required
def admin_add_teacher(request):
    admin_dept = get_admin_department(request)
    return render(request, 'ADMIN/Admin_Add_Teacher.html', {
        'admin_dept': admin_dept,
    })


# =====================================================
# ADMIN — ATTENDANCE AJAX
# =====================================================

@login_required
@csrf_protect
@require_http_methods(["GET", "POST"])
def save_attendance(request):
    admin_dept = get_admin_department(request)

    if request.method == 'GET':
        date_str = request.GET.get('date') or date_cls.today().isoformat()
        records = Attendance.objects.filter(date=date_str)

        if admin_dept:
            records = records.filter(student__department=admin_dept)

        data = [
            {
                'student_id': r.student_id,
                'timeInAM': r.time_in_am.strftime('%H:%M') if r.time_in_am else '',
                'timeOutAM': r.time_out_am.strftime('%H:%M') if r.time_out_am else '',
                'timeInPM': r.time_in_pm.strftime('%H:%M') if r.time_in_pm else '',
                'timeOutPM': r.time_out_pm.strftime('%H:%M') if r.time_out_pm else '',
                'status': r.status,
            }
            for r in records
        ]
        return JsonResponse({'success': True, 'records': data})

    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)

    student_id = payload.get('student_id')
    field = payload.get('field')
    value = payload.get('value', '')
    date_str = payload.get('date') or date_cls.today().isoformat()

    try:
        student = Student.objects.get(id=student_id)
    except Student.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Student not found'}, status=404)

    if admin_dept and student.department != admin_dept:
        return JsonResponse({'success': False, 'error': 'Not authorized'}, status=403)

    field_map = {
        'timeInAM':  'time_in_am',
        'timeOutAM': 'time_out_am',
        'timeInPM':  'time_in_pm',
        'timeOutPM': 'time_out_pm',
    }

    if field not in field_map:
        return JsonResponse({'success': False, 'error': 'Invalid field'}, status=400)

    record, _ = Attendance.objects.get_or_create(
        student_id=student_id,
        date=date_str,
    )
    setattr(record, field_map[field], value or None)

    if any([record.time_in_am, record.time_out_am, record.time_in_pm, record.time_out_pm]):
        if record.time_in_am and record.time_in_am > time_cls(8, 0):
            record.status = 'late'
        else:
            record.status = 'present'
    else:
        record.status = 'absent'

    record.save()
    return JsonResponse({'success': True})


@login_required
@csrf_protect
@require_http_methods(["POST"])
def bulk_attendance(request):
    admin_dept = get_admin_department(request)

    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)

    action = payload.get('action')
    date_str = payload.get('date') or date_cls.today().isoformat()
    student_ids = payload.get('student_ids', [])

    if action not in ('present', 'absent', 'clear'):
        return JsonResponse({'success': False, 'error': 'Invalid action'}, status=400)

    for sid in student_ids:
        try:
            student = Student.objects.get(id=sid)
        except Student.DoesNotExist:
            continue

        if admin_dept and student.department != admin_dept:
            continue

        record, _ = Attendance.objects.get_or_create(
            student_id=sid, date=date_str,
        )

        if action == 'present':
            record.time_in_am  = time_cls(7, 30)
            record.time_out_am = time_cls(11, 30)
            record.time_in_pm  = time_cls(12, 30)
            record.time_out_pm = time_cls(16, 30)
            record.status = 'present'
        else:
            record.time_in_am  = None
            record.time_out_am = None
            record.time_in_pm  = None
            record.time_out_pm = None
            record.status = 'absent'

        record.save()

    return JsonResponse({'success': True, 'updated': len(student_ids)})


@login_required
@csrf_protect
@require_http_methods(["POST"])
def reset_attendance(request):
    admin_dept = get_admin_department(request)

    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)

    date_str = payload.get('date') or date_cls.today().isoformat()

    qs = Attendance.objects.filter(date=date_str)
    if admin_dept:
        qs = qs.filter(student__department=admin_dept)

    qs.delete()
    return JsonResponse({'success': True})


# =====================================================
# TEACHER
# =====================================================

@login_required
def teacher_dashboard(request):
    return render(request, 'TEACHER/Teacher_Dashboard.html')


@login_required
def teacher_class_attendance(request):
    return render(request, 'TEACHER/Teacher_Class_Attendance.html')


@login_required
def teacher_class_record(request):
    return render(request, 'TEACHER/Teacher_Class_Record.html')


@login_required
def teacher_profile(request):
    return render(request, 'TEACHER/Teacher_Personal_Info.html')


@login_required
def teacher_history(request):
    return render(request,'TEACHER/Teacher_History.html')
@login_required
def teacher_security(request):
    return render(request, 'TEACHER/Teacher_Security.html')