import random
import string
from django.db import IntegrityError
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q  # Added this for search functionality
from .models import Student, Program, Enrollment, Notification
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
                
                # --- ROBUST UNIQUE ID GENERATOR ---
                unique_id_found = False
                while not unique_id_found:
                    random_suffix = ''.join(random.choices(string.digits, k=4))
                    potential_id = f"{timezone.now().year}-{random_suffix}"
                    
                    # Check if this ID already exists in the database
                    if not Student.objects.filter(student_id=potential_id).exists():
                        student.student_id = potential_id
                        unique_id_found = True
                
                student.save()
                login(request, user)
                messages.success(request, f'Registration successful! Your Student ID is {student.student_id}')
                return redirect('dashboard')
            except IntegrityError:
                messages.error(request, 'A database error occurred. Please try again.')
        else:
            # DEBUG: This prints exactly what's wrong to your terminal/cmd
            print("Form Errors:", form.errors)
            print("Profile Errors:", profile_form.errors)
            messages.error(request, 'Registration failed. Please check the errors highlighted in the form.')
    else:
        form = RegisterForm()
        profile_form = StudentProfileForm()
    
    return render(request, 'registration/register.html', {
        'form': form,
        'profile_form': profile_form
    })

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            role = "Admin" if user.is_staff else "Student"
            messages.success(request, f'Welcome back! ({role})')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'registration/login.html')

def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('login')

# ============================================
# DASHBOARD
# ============================================

@login_required
def dashboard_view(request):
    # Cleaner way to get student profile using getattr
    student = getattr(request.user, 'student_profile', None)
    
    # Get notifications
    unread_notifications = Notification.objects.filter(
        user=request.user, 
        is_read=False
    ).count()
    
    # Admin view
    if request.user.is_staff:
        total_students = Student.objects.count()
        total_programs = Program.objects.filter(is_active=True).count()
        pending_enrollments = Enrollment.objects.filter(status='pending').count()
        approved_enrollments = Enrollment.objects.filter(status='approved').count()
        
        recent_enrollments = Enrollment.objects.filter(
            status='pending'
        ).order_by('-created_at')[:5]
        
        context = {
            'is_admin': True,
            'student': student,
            'total_students': total_students,
            'total_programs': total_programs,
            'pending_enrollments': pending_enrollments,
            'approved_enrollments': approved_enrollments,
            'recent_enrollments': recent_enrollments,
            'unread_notifications': unread_notifications,
        }
    else:
        # Student view
        if student:
            my_enrollments = Enrollment.objects.filter(student=student)
            pending_count = my_enrollments.filter(status='pending').count()
            approved_count = my_enrollments.filter(status='approved').count()
            enrolled_count = my_enrollments.filter(status='enrolled').count()
            recent_enrollments = my_enrollments[:5]
        else:
            pending_count = 0
            approved_count = 0
            enrolled_count = 0
            recent_enrollments = []
        
        available_programs = Program.objects.filter(is_active=True)[:6]
        
        context = {
            'is_admin': False,
            'student': student,
            'pending_count': pending_count,
            'approved_count': approved_count,
            'enrolled_count': enrolled_count,
            'recent_enrollments': recent_enrollments,
            'available_programs': available_programs,
            'unread_notifications': unread_notifications,
        }
    
    return render(request, 'enrollments/dashboard.html', context)

# ============================================
# PROGRAM MANAGEMENT
# ============================================

@login_required
def program_list_view(request):
    programs = Program.objects.all()
    search = request.GET.get('search', '')
    program_type = request.GET.get('type', '')
    status = request.GET.get('status', '')
    
    if search:
        programs = programs.filter(
            Q(code__icontains=search) |
            Q(name__icontains=search) |
            Q(description__icontains=search)
        )
    
    if program_type:
        programs = programs.filter(program_type=program_type)
    
    if status:
        programs = programs.filter(is_active=(status == 'active'))
    
    context = {
        'programs': programs,
        'search': search,
        'program_type': program_type,
        'status': status,
    }
    return render(request, 'enrollments/program_list.html', context)

@login_required
def program_detail_view(request, pk):
    program = get_object_or_404(Program, pk=pk)
    enrollment_count = Enrollment.objects.filter(program=program).count()
    return render(request, 'enrollments/program_detail.html', {
        'program': program,
        'enrollment_count': enrollment_count,
    })

@login_required
def program_create_view(request):
    if not request.user.is_staff:
        messages.error(request, 'Only admins can add programs.')
        return redirect('program_list')
    
    if request.method == 'POST':
        form = ProgramForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Program created successfully!')
            return redirect('program_list')
    else:
        form = ProgramForm()
    return render(request, 'enrollments/program_form.html', {'form': form, 'action': 'Create'})

@login_required
def program_update_view(request, pk):
    if not request.user.is_staff:
        messages.error(request, 'Only admins can edit programs.')
        return redirect('program_list')
    
    program = get_object_or_404(Program, pk=pk)
    if request.method == 'POST':
        form = ProgramForm(request.POST, instance=program)
        if form.is_valid():
            form.save()
            messages.success(request, 'Program updated successfully!')
            return redirect('program_detail', pk=pk)
    else:
        form = ProgramForm(instance=program)
    return render(request, 'enrollments/program_form.html', {'form': form, 'action': 'Update'})

@login_required
def program_delete_view(request, pk):
    if not request.user.is_staff:
        messages.error(request, 'Only admins can delete programs.')
        return redirect('program_list')
    
    program = get_object_or_404(Program, pk=pk)
    if request.method == 'POST':
        program.delete()
        messages.success(request, 'Program deleted successfully!')
        return redirect('program_list')
    return render(request, 'enrollments/program_confirm_delete.html', {'program': program})

# ============================================
# ENROLLMENT MANAGEMENT
# ============================================

@login_required
def enrollment_list_view(request):
    student = getattr(request.user, 'student_profile', None)
    view_mode = request.GET.get('view', 'all' if request.user.is_staff else 'my')
    
    if request.user.is_staff:
        if view_mode == 'my' and student:
            enrollments = Enrollment.objects.filter(student=student)
            title = "My Enrollments"
        else:
            enrollments = Enrollment.objects.all()
            title = "All Enrollments (Admin View)"
    else:
        enrollments = Enrollment.objects.filter(student=student) if student else Enrollment.objects.none()
        title = "My Enrollments"
    
    status = request.GET.get('status', '')
    if status:
        enrollments = enrollments.filter(status=status)
    
    return render(request, 'enrollments/enrollment_list.html', {
        'enrollments': enrollments,
        'status': status,
        'view_mode': view_mode,
        'title': title,
        'student': student,
    })

@login_required
def enrollment_create_view(request):
    student = getattr(request.user, 'student_profile', None)
    if not student:
        messages.error(request, 'Please complete your student profile first.')
        return redirect('student_profile')
    
    if request.method == 'POST':
        form = EnrollmentForm(request.POST)
        if form.is_valid():
            enrollment = form.save(commit=False)
            enrollment.student = student
            
            if request.user.is_staff and request.POST.get('auto_approve'):
                enrollment.status = 'approved'
                enrollment.reviewed_by = request.user
                enrollment.reviewed_at = timezone.now()
                messages.success(request, 'Enrollment created and auto-approved!')
            else:
                enrollment.status = 'pending'
                messages.success(request, 'Enrollment submitted! Waiting for approval.')
            
            enrollment.save()
            return redirect('enrollment_list')
    else:
        form = EnrollmentForm()
    
    return render(request, 'enrollments/enrollment_form.html', {
        'form': form, 
        'action': 'Create', 
        'student': student
    })

@login_required
def enrollment_update_view(request, pk):
    enrollment = get_object_or_404(Enrollment, pk=pk)
    student = getattr(request.user, 'student_profile', None)
    
    if not request.user.is_staff and enrollment.student != student:
        messages.error(request, 'Access denied.')
        return redirect('enrollment_list')
    
    if enrollment.status != 'pending' and not request.user.is_staff:
        messages.error(request, 'You can only edit pending enrollments.')
        return redirect('enrollment_list')
    
    if request.method == 'POST':
        form = EnrollmentForm(request.POST, instance=enrollment)
        if form.is_valid():
            form.save()
            messages.success(request, 'Enrollment updated successfully!')
            return redirect('enrollment_list')
    else:
        form = EnrollmentForm(instance=enrollment)
    
    return render(request, 'enrollments/enrollment_form.html', {
        'form': form,
        'action': 'Update',
        'enrollment': enrollment
    })

@login_required
def enrollment_delete_view(request, pk):
    enrollment = get_object_or_404(Enrollment, pk=pk)
    student = getattr(request.user, 'student_profile', None)
    
    if not request.user.is_staff and enrollment.student != student:
        messages.error(request, 'Access denied.')
        return redirect('enrollment_list')
    
    if request.method == 'POST':
        enrollment.delete()
        messages.success(request, 'Enrollment deleted successfully!')
        return redirect('enrollment_list')
    return render(request, 'enrollments/enrollment_confirm_delete.html', {'enrollment': enrollment})

# ============================================
# ADMIN APPROVAL SYSTEM
# ============================================

@login_required
def enrollment_approve_view(request, pk):
    if not request.user.is_staff:
        messages.error(request, 'Only admins can approve enrollments.')
        return redirect('enrollment_list')
    
    enrollment = get_object_or_404(Enrollment, pk=pk, status='pending')
    
    if request.method == 'POST':
        admin_notes = request.POST.get('admin_notes', '')
        enrollment.status = 'approved'
        enrollment.reviewed_by = request.user
        enrollment.reviewed_at = timezone.now()
        enrollment.admin_notes = admin_notes
        enrollment.save()
        
        Notification.objects.create(
            user=enrollment.student.user,
            notification_type='enrollment_approved',
            enrollment=enrollment,
            message=f'Your enrollment for {enrollment.program.name} has been approved!'
        )
        messages.success(request, f'Enrollment approved for {enrollment.student.get_full_name()}!')
        return redirect('enrollment_list')
    
    return render(request, 'enrollments/enrollment_approve.html', {'enrollment': enrollment})

@login_required
def enrollment_reject_view(request, pk):
    if not request.user.is_staff:
        messages.error(request, 'Only admins can reject enrollments.')
        return redirect('enrollment_list')
    
    enrollment = get_object_or_404(Enrollment, pk=pk, status='pending')
    
    if request.method == 'POST':
        admin_notes = request.POST.get('admin_notes', '')
        if not admin_notes:
            messages.error(request, 'Please provide a reason for rejection.')
            return render(request, 'enrollments/enrollment_reject.html', {'enrollment': enrollment})
        
        enrollment.status = 'rejected'
        enrollment.reviewed_by = request.user
        enrollment.reviewed_at = timezone.now()
        enrollment.admin_notes = admin_notes
        enrollment.save()
        
        Notification.objects.create(
            user=enrollment.student.user,
            notification_type='enrollment_rejected',
            enrollment=enrollment,
            message=f'Your enrollment for {enrollment.program.name} has been rejected. Reason: {admin_notes}'
        )
        messages.success(request, 'Enrollment rejected and student notified.')
        return redirect('enrollment_list')
    
    return render(request, 'enrollments/enrollment_reject.html', {'enrollment': enrollment})

# ============================================
# NOTIFICATIONS
# ============================================

@login_required
def notifications_view(request):
    notifications = Notification.objects.filter(user=request.user)
    if request.GET.get('mark_read'):
        notifications.update(is_read=True)
        messages.success(request, 'All notifications marked as read.')
        return redirect('notifications')
    
    return render(request, 'enrollments/notifications.html', {
        'notifications': notifications,
        'unread_count': notifications.filter(is_read=False).count(),
    })

@login_required
def notification_read_view(request, pk):
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.is_read = True
    notification.save()
    return redirect('enrollment_list')

# ============================================
# STUDENT PROFILE
# ============================================

@login_required
def student_profile_view(request):
    # Safely get the student profile if it exists
    student = getattr(request.user, 'student_profile', None)
    
    if request.method == 'POST':
        # Pass the instance so we update the existing profile instead of creating a new one
        form = StudentProfileForm(request.POST, request.FILES, instance=student)
        
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Please correct the errors in your profile.')
    else:
        # If no profile exists, instance will be None (blank form)
        form = StudentProfileForm(instance=student)
    
    # Passing 'student' here is crucial for the read-only Student ID field in your HTML
    return render(request, 'enrollments/student_profile.html', {
        'form': form,
        'student': student
    })