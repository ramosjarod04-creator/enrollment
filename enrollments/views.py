import random
import string
from django.db import IntegrityError
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from .models import Student, Program, Enrollment, Notification, SchoolYear
from .forms import RegisterForm, StudentProfileForm, EnrollmentForm, ProgramForm

# ============================================
# AUTHENTICATION
# ============================================

def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        profile_form = StudentProfileForm(request.POST, request.FILES)
        if form.is_valid() and profile_form.is_valid():
            try:
                user = form.save()
                student = profile_form.save(commit=False)
                student.user = user
                unique_id_found = False
                while not unique_id_found:
                    random_suffix = ''.join(random.choices(string.digits, k=4))
                    potential_id = f"{timezone.now().year}-{random_suffix}"
                    if not Student.objects.filter(student_id=potential_id).exists():
                        student.student_id = potential_id
                        unique_id_found = True
                student.save()
                login(request, user)
                messages.success(request, f'Registration successful! ID: {student.student_id}')
                return redirect('dashboard')
            except IntegrityError:
                messages.error(request, 'A database error occurred.')
    else:
        form = RegisterForm()
        profile_form = StudentProfileForm()
    return render(request, 'registration/register.html', {'form': form, 'profile_form': profile_form})

def login_view(request):
    if request.user.is_authenticated: return redirect('dashboard')
    if request.method == 'POST':
        user = authenticate(request, username=request.POST.get('username'), password=request.POST.get('password'))
        if user:
            login(request, user)
            messages.success(request, 'Welcome back!')
            return redirect('dashboard')
        messages.error(request, 'Invalid credentials.')
    return render(request, 'registration/login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

# ============================================
# DASHBOARD
# ============================================

@login_required
def dashboard_view(request):
    student = getattr(request.user, 'student_profile', None)
    unread_notifications = Notification.objects.filter(user=request.user, is_read=False).count()
    
    if request.user.is_staff:
        context = {
            'is_admin': True,
            'total_students': Student.objects.count(),
            'total_programs': Program.objects.filter(is_active=True).count(),
            'approved_enrollments': Enrollment.objects.filter(status__in=['approved', 'enrolled']).count(),
            'pending_enrollments': Enrollment.objects.filter(status='pending').count(),
            'display_courses': Program.objects.all(),
        }
    else:
        # Get all enrollments for this student
        my_enr = Enrollment.objects.filter(student=student) if student else Enrollment.objects.none()
        
        # Get IDs of programs the student has already applied for (to hide them from 'Available')
        applied_ids = my_enr.values_list('program_id', flat=True)
        
        # Filter enrollments that are officially "done" (Approved or Enrolled)
        active_enrollments = my_enr.filter(status__in=['approved', 'enrolled'])

        context = {
            'is_admin': False,
            'student': student,
            'pending_count': my_enr.filter(status='pending').count(),
            'approved_count': my_enr.filter(status='approved').count(),
            'enrolled_count': active_enrollments.count(), # This fixes the '0' in the Enrolled card
            'display_courses': active_enrollments,        # This fixes the "No active enrollments found" list
            'available_courses': Program.objects.filter(is_active=True).exclude(id__in=applied_ids),
            'recent_applications': my_enr.filter(status='pending').order_by('-created_at')[:2],
            'reg_code': student.registration_code if student else None,
        }
    context['unread_notifications'] = unread_notifications
    return render(request, 'enrollments/dashboard.html', context)

# ============================================
# PROGRAM MANAGEMENT
# ============================================

@login_required
def program_list_view(request):
    programs = Program.objects.all()
    search = request.GET.get('search', '')
    if search: programs = programs.filter(Q(code__icontains=search) | Q(name__icontains=search))
    return render(request, 'enrollments/program_list.html', {'programs': programs, 'search': search})

@login_required
def program_detail_view(request, pk):
    return render(request, 'enrollments/program_detail.html', {'program': get_object_or_404(Program, pk=pk)})

@login_required
def program_create_view(request):
    if not request.user.is_staff: return redirect('program_list')
    form = ProgramForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('program_list')
    return render(request, 'enrollments/program_form.html', {'form': form, 'action': 'Create'})

# (Simplified remaining program views for brevity, keeping your existing logic)
@login_required
def program_update_view(request, pk):
    if not request.user.is_staff: return redirect('program_list')
    program = get_object_or_404(Program, pk=pk)
    form = ProgramForm(request.POST or None, instance=program)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('program_detail', pk=pk)
    return render(request, 'enrollments/program_form.html', {'form': form, 'action': 'Update'})

@login_required
def program_delete_view(request, pk):
    if not request.user.is_staff: return redirect('program_list')
    program = get_object_or_404(Program, pk=pk)
    if request.method == 'POST':
        program.delete()
        return redirect('program_list')
    return render(request, 'enrollments/program_confirm_delete.html', {'program': program})

# ============================================
# ENROLLMENT MANAGEMENT
# ============================================

@login_required
def enrollment_create_view(request):
    student = getattr(request.user, 'student_profile', None)
    if not student:
        messages.error(request, 'Please complete your profile first.')
        return redirect('student_profile')
    
    if request.method == 'POST':
        program_id = request.POST.get('program')
        if program_id:
            program = get_object_or_404(Program, id=program_id)
            if Enrollment.objects.filter(student=student, program=program).exclude(status='rejected').exists():
                messages.warning(request, 'Application already exists.')
                return redirect('dashboard')

            # FIXED: Correct fields for SchoolYear based on your model
            sy_obj, created = SchoolYear.objects.get_or_create(
                year_start=2025, 
                year_end=2026, 
                semester='1st',
                defaults={
                    'enrollment_start': timezone.now().date(),
                    'enrollment_end': timezone.now().date() + timezone.timedelta(days=30)
                }
            )

            Enrollment.objects.create(
                student=student, 
                program=program, 
                school_year=sy_obj,
                year_level='1',  # Added missing required field
                status='pending'
            )
            messages.success(request, 'Enrollment submitted!')
            return redirect('dashboard')
    return redirect('program_list')

@login_required
def enrollment_list_view(request):
    student = getattr(request.user, 'student_profile', None)
    enrollments = Enrollment.objects.all() if request.user.is_staff else Enrollment.objects.filter(student=student)
    return render(request, 'enrollments/enrollment_list.html', {'enrollments': enrollments.order_by('-created_at')})

@login_required
def enrollment_update_view(request, pk):
    enrollment = get_object_or_404(Enrollment, pk=pk)
    if not request.user.is_staff and enrollment.student.user != request.user: return redirect('dashboard')
    form = EnrollmentForm(request.POST or None, instance=enrollment)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('enrollment_list')
    return render(request, 'enrollments/enrollment_form.html', {'form': form, 'action': 'Update'})

@login_required
def enrollment_delete_view(request, pk):
    enrollment = get_object_or_404(Enrollment, pk=pk)
    if not request.user.is_staff and enrollment.student.user != request.user: return redirect('dashboard')
    if request.method == 'POST':
        enrollment.delete()
        return redirect('enrollment_list')
    return render(request, 'enrollments/enrollment_confirm_delete.html', {'enrollment': enrollment})

# ============================================
# ADMIN ACTIONS
# ============================================

@login_required
def enrollment_approve_view(request, pk):
    if not request.user.is_staff: return redirect('dashboard')
    enrollment = get_object_or_404(Enrollment, pk=pk, status='pending')
    if request.method == 'POST':
        enrollment.status = 'approved'
        enrollment.reviewed_by = request.user
        enrollment.reviewed_at = timezone.now()
        enrollment.admin_notes = request.POST.get('admin_notes', '') 
        enrollment.save()
        
        Notification.objects.create(
            user=enrollment.student.user,
            notification_type='enrollment_approved',
            enrollment=enrollment, # Added missing required field
            message=f'Your enrollment for {enrollment.program.name} has been approved!'
        )
        return redirect('dashboard')
    return render(request, 'enrollments/enrollment_approve.html', {'enrollment': enrollment, 'is_approve': True})

@login_required
def enrollment_reject_view(request, pk):
    if not request.user.is_staff: return redirect('dashboard')
    enrollment = get_object_or_404(Enrollment, pk=pk, status='pending')
    if request.method == 'POST':
        enrollment.status = 'rejected'
        enrollment.reviewed_by = request.user
        enrollment.reviewed_at = timezone.now()
        enrollment.admin_notes = request.POST.get('admin_notes', '')
        enrollment.save()
        
        Notification.objects.create(
            user=enrollment.student.user,
            notification_type='enrollment_rejected',
            enrollment=enrollment, # Added missing required field
            message=f'Your enrollment for {enrollment.program.name} has been rejected.'
        )
        return redirect('dashboard')
    return render(request, 'enrollments/enrollment_approve.html', {'enrollment': enrollment, 'is_approve': False})

# ============================================
# NOTIFICATIONS & PROFILE
# ============================================

@login_required
def notifications_view(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'enrollments/notifications.html', {'notifications': notifications})

@login_required
def notification_read_view(request, pk):
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.is_read = True
    notification.save()
    return redirect('notifications')

@login_required
def student_profile_view(request):
    student = getattr(request.user, 'student_profile', None)
    form = StudentProfileForm(request.POST or None, request.FILES or None, instance=student)
    if request.method == 'POST' and form.is_valid():
        profile = form.save(commit=False)
        profile.user = request.user
        profile.save()
        return redirect('dashboard')
    return render(request, 'enrollments/student_profile.html', {'form': form, 'student': student})
