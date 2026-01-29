from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Student, Program, SchoolYear, Enrollment

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    
    class Meta:
        model = User
        # Removed password fields as UserCreationForm handles those automatically
        fields = ['username', 'email']

class StudentProfileForm(forms.ModelForm):
    class Meta:
        model = Student
        # FIX: Exclude 'user' and 'student_id' because they are handled in views.py
        exclude = ['user', 'student_id']
        
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-input'}),
            'middle_name': forms.TextInput(attrs={'class': 'form-input'}),
            'last_name': forms.TextInput(attrs={'class': 'form-input'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'contact_number': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '+63 XXX XXX XXXX'}),
            'email': forms.EmailInput(attrs={'class': 'form-input'}),
            'address': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            'guardian_name': forms.TextInput(attrs={'class': 'form-input'}),
            'guardian_contact': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '+63 XXX XXX XXXX'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-input'}),
        }

class ProgramForm(forms.ModelForm):
    class Meta:
        model = Program
        fields = ['code', 'name', 'program_type', 'description', 'duration_years', 
                  'tuition_fee', 'is_active']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g., BSCS'}),
            'name': forms.TextInput(attrs={'class': 'form-input'}),
            'program_type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 4}),
            'duration_years': forms.NumberInput(attrs={'class': 'form-input'}),
            'tuition_fee': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }

class SchoolYearForm(forms.ModelForm):
    class Meta:
        model = SchoolYear
        fields = ['year_start', 'year_end', 'semester', 'is_active', 
                  'enrollment_start', 'enrollment_end']
        widgets = {
            'year_start': forms.NumberInput(attrs={'class': 'form-input'}),
            'year_end': forms.NumberInput(attrs={'class': 'form-input'}),
            'semester': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'enrollment_start': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'enrollment_end': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
        }

class EnrollmentForm(forms.ModelForm):
    class Meta:
        model = Enrollment
        # enrollment_id is generated in the model save() method, so we exclude it here
        fields = ['program', 'school_year', 'year_level']
        widgets = {
            'program': forms.Select(attrs={'class': 'form-select'}),
            'school_year': forms.Select(attrs={'class': 'form-select'}),
            'year_level': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show active programs and school years to prevent enrolling in closed terms
        self.fields['program'].queryset = Program.objects.filter(is_active=True)
        self.fields['school_year'].queryset = SchoolYear.objects.filter(is_active=True)