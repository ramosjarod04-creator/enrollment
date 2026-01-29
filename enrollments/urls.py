from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('', views.dashboard_view, name='dashboard'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Student Profile
    path('profile/', views.student_profile_view, name='student_profile'),
    
    # Programs
    path('programs/', views.program_list_view, name='program_list'),
    path('programs/<int:pk>/', views.program_detail_view, name='program_detail'),
    path('programs/create/', views.program_create_view, name='program_create'),
    path('programs/<int:pk>/update/', views.program_update_view, name='program_update'),
    path('programs/<int:pk>/delete/', views.program_delete_view, name='program_delete'),
    
    # Enrollments
    path('enrollments/', views.enrollment_list_view, name='enrollment_list'),
    path('enrollments/create/', views.enrollment_create_view, name='enrollment_create'),
    path('enrollments/<int:pk>/update/', views.enrollment_update_view, name='enrollment_update'),
    path('enrollments/<int:pk>/delete/', views.enrollment_delete_view, name='enrollment_delete'),
    
    # Admin approval
    path('enrollments/<int:pk>/approve/', views.enrollment_approve_view, name='enrollment_approve'),
    path('enrollments/<int:pk>/reject/', views.enrollment_reject_view, name='enrollment_reject'),
    
    # Notifications
    path('notifications/', views.notifications_view, name='notifications'),
    path('notifications/<int:pk>/read/', views.notification_read_view, name='notification_read'),
]

