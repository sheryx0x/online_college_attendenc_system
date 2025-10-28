 
# attendance/utils.py
from django.core.mail import send_mail
from django.conf import settings

def send_attendance_alert(email, student_name, attendance_percentage):
    subject = 'Attendance Alert'
    message = f'Dear Teacher,\n\nThe attendance for {student_name} has dropped to {attendance_percentage}%.\n\nBest Regards,\nYour College Attendance System'
    send_mail(subject, message, settings.EMAIL_HOST_USER, [email])
