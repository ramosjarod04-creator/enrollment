from django.contrib import admin
from .models import Student, Program, SchoolYear, Enrollment, Notification


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['student_id', 'get_full_name', 'email', 'contact_number', 'created_at']
    search_fields = ['student_id', 'first_name', 'last_name', 'email']
    list_filter = ['gender', 'created_at']


@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'program_type', 'duration_years', 'tuition_fee', 'is_active']
    list_filter = ['program_type', 'is_active']
    search_fields = ['code', 'name']


@admin.register(SchoolYear)
class SchoolYearAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'is_active', 'enrollment_start', 'enrollment_end']
    list_filter = ['is_active', 'semester']


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ['enrollment_id', 'student', 'program', 'school_year', 'year_level', 'status', 'reviewed_by']
    list_filter = ['status', 'year_level', 'school_year', 'reviewed_by']
    search_fields = ['enrollment_id', 'student__first_name', 'student__last_name']
    readonly_fields = ['enrollment_id', 'reviewed_by', 'reviewed_at']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'notification_type', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read']
    search_fields = ['user__username', 'message']