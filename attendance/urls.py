from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from .views import MyPasswordResetView
urlpatterns = [
    path('', views.home, name='home'),
    path('signup/', views.signup, name='signup'),
    path('student/<int:student_id>/edit/', views.edit_student, name='edit_student'),
    path('signin/', views.signin, name='signin'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('search/', views.search_attendance, name='search_attendance'),
    path('search_results/', views.search_attendance, name='search_attendance'),
    path('logout/', views.logout_view, name='logout'),
    path('class/<int:class_id>/attendance_dates/', views.attendance_dates, name='attendance_dates'),
    path('class/<int:class_id>/attendance_records/<str:date>/', views.attendance_records, name='attendance_records'),
    path('create_class/', views.create_class, name='create_class'),
    path('class/<int:class_id>/', views.class_detail, name='class_detail'),
    path('class/<int:class_id>/edit/', views.edit_class, name='edit_class'),
    path('class/<int:class_id>/delete/', views.delete_class, name='delete_class'),
    path('class/<int:class_id>/take_attendance/', views.take_attendance, name='take_attendance'),
    path('class/<int:class_id>/attendance_history/', views.attendance_history, name='attendance_history'),
    path('class/<int:class_id>/generate_report/', views.generate_report, name='generate_report'),
    path('password_reset/', MyPasswordResetView.as_view(), name='password_reset'),
    path('password_reset_done/', auth_views.PasswordResetDoneView.as_view(
        template_name="attendance/password_reset_done.html"), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name="attendance/password_reset_confirm.html"), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name="attendance/password_reset_complete.html"), name='password_reset_complete'),
]
