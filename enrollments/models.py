from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.db import transaction # Added for safe ID generation

class Student(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    student_id = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    contact_number = models.CharField(max_length=20)
    email = models.EmailField()
    address = models.TextField()
    guardian_name = models.CharField(max_length=200)
    guardian_contact = models.CharField(max_length=20)
    profile_picture = models.ImageField(upload_to='students/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['last_name', 'first_name']
    
    def __str__(self):
        return f"{self.student_id} - {self.get_full_name()}"
    
    def get_full_name(self):
        middle = f"{self.middle_name} " if self.middle_name else ""
        return f"{self.first_name} {middle}{self.last_name}"


class Program(models.Model):
    PROGRAM_TYPES = [
        ('undergraduate', 'Undergraduate'),
        ('graduate', 'Graduate'),
        ('vocational', 'Vocational'),
    ]
    
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    program_type = models.CharField(max_length=20, choices=PROGRAM_TYPES)
    description = models.TextField()
    duration_years = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)])
    tuition_fee = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class SchoolYear(models.Model):
    SEMESTER_CHOICES = [
        ('1st', '1st Semester'),
        ('2nd', '2nd Semester'),
        ('summer', 'Summer'),
    ]
    
    year_start = models.IntegerField()
    year_end = models.IntegerField()
    semester = models.CharField(max_length=10, choices=SEMESTER_CHOICES)
    is_active = models.BooleanField(default=True)
    enrollment_start = models.DateField()
    enrollment_end = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-year_start', '-year_end']
        unique_together = ['year_start', 'year_end', 'semester']
    
    def __str__(self):
        return f"SY {self.year_start}-{self.year_end} ({self.get_semester_display()})"


class Enrollment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('enrolled', 'Enrolled'),
        ('dropped', 'Dropped'),
    ]
    
    YEAR_LEVEL_CHOICES = [
        ('1', '1st Year'),
        ('2', '2nd Year'),
        ('3', '3rd Year'),
        ('4', '4th Year'),
        ('5', '5th Year'),
    ]
    
    enrollment_id = models.CharField(max_length=20, unique=True, editable=False) # Editable=False keeps it safe from forms
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='enrollments')
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='enrollments')
    school_year = models.ForeignKey(SchoolYear, on_delete=models.CASCADE, related_name='enrollments')
    year_level = models.CharField(max_length=1, choices=YEAR_LEVEL_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_enrollments')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    admin_notes = models.TextField(blank=True, null=True) # Added null=True for database flexibility
    
    total_fee = models.DecimalField(max_digits=10, decimal_places=2, blank=True) # Allowed blank so it can auto-populate
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        # Prevent double enrollment in same SY/Semester
        unique_together = ['student', 'program', 'school_year']

    def __str__(self):
        return f"{self.enrollment_id} - {self.student.get_full_name()} - {self.program.code}"
    
    def save(self, *args, **kwargs):
        # Auto-set tuition fee from program if not provided
        if not self.total_fee and self.program:
            self.total_fee = self.program.tuition_fee
            
        if not self.enrollment_id:
            with transaction.atomic(): # Ensure thread safety
                year = timezone.now().year
                # Get the highest current count for this year to avoid collisions
                last_enrollment = Enrollment.objects.filter(
                    enrollment_id__startswith=f'ENR-{year}'
                ).order_by('enrollment_id').last()
                
                if last_enrollment:
                    last_id_parts = last_enrollment.enrollment_id.split('-')
                    new_count = int(last_id_parts[2]) + 1
                else:
                    new_count = 1
                    
                self.enrollment_id = f'ENR-{year}-{new_count:05d}'
                super().save(*args, **kwargs)
        else:
            super().save(*args, **kwargs)


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('enrollment_approved', 'Enrollment Approved'),
        ('enrollment_rejected', 'Enrollment Rejected'),
        ('enrollment_confirmed', 'Enrollment Confirmed'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enrollment_notifications')
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES)
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.notification_type}"