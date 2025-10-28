from django.shortcuts import render, redirect,get_object_or_404,HttpResponse
from django.contrib.auth import login, authenticate,logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from datetime import datetime,timedelta
from .forms import SignUpForm, ClassForm, StudentForm,EditStudentForm
from .models import Student, Teacher, Class, ClassStudent, Attendance,Department
from django.template.loader import render_to_string
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from datetime import date
from django.core.mail import send_mail
from django.conf import settings

from django.shortcuts import render
from django.http import JsonResponse
from .models import Attendance, Class, Department

def home(request):
    attendance_records = None
    departments = Department.objects.all()
    classes = None

    
    department_id = request.GET.get('department_id')

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':  
        if department_id:
            try:
                department = Department.objects.get(id=department_id)
                classes = list(Class.objects.filter(department=department).values('id', 'name'))
                return JsonResponse({'classes': classes})
            except Department.DoesNotExist:
                return JsonResponse({'error': 'Department not found'}, status=404)

    
    if request.method == 'GET':
        
        student_name = request.GET.get('student_name')
        roll_no = request.GET.get('roll_no')
        class_id = request.GET.get('class')

        if student_name and class_id:
            attendance_records = Attendance.objects.filter(
                class_student__student__name__icontains=student_name,
                class_student__class_name_id=class_id
            )
        elif student_name:
            attendance_records = Attendance.objects.filter(
                class_student__student__name__icontains=student_name
            )

    return render(request, 'attendance/home.html', {
        'attendance_records': attendance_records,
        'departments': departments,
        'classes': classes,
    })



def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
           
            user = form.save()
            
            Teacher.objects.create(user=user, name=user.username, email=form.cleaned_data['email'])
            
            login(request, user)
            return redirect('home')  
    else:
        form = SignUpForm()
    
    return render(request, 'attendance/signup.html', {'form': form})

def signin(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
           
            return render(request, 'attendance/signin.html', {'error': 'Invalid username or password'})
    return render(request, 'attendance/signin.html')



def logout_view(request):
    logout(request)
    return redirect('home')


@login_required
def dashboard(request):
    teacher = Teacher.objects.get(user=request.user)
    departments = Department.objects.all()

    classes = Class.objects.filter(teacher=teacher)
    return render(request, 'attendance/dashboard.html', {
        'departments': departments,
        'classes': classes,
    }
)

@login_required
def create_class(request):
    if request.method == 'POST':
        form = ClassForm(request.POST)
        if form.is_valid():
            class_instance = form.save(commit=False)
            class_instance.teacher = Teacher.objects.get(user=request.user)
            class_instance.save()
            return redirect('dashboard')
    else:
        form = ClassForm()
    return render(request, 'attendance/create_class.html', {'form': form})


@login_required
def delete_class(request, class_id):
    class_instance = get_object_or_404(Class, id=class_id, teacher__user=request.user)
    class_instance.delete()
    messages.success(request, "Class deleted successfully.")
    return redirect('dashboard')


@login_required
def edit_class(request, class_id):
    class_instance = get_object_or_404(Class, id=class_id, teacher__user=request.user)

    if request.method == 'POST':
        form = ClassForm(request.POST, instance=class_instance)
        if form.is_valid():
            form.save()
            messages.success(request, "Class updated successfully.")
            return redirect('class_detail', class_id=class_instance.id)
    else:
        form = ClassForm(instance=class_instance)

    return render(request, 'attendance/edit_class.html', {'form': form, 'class_instance': class_instance})


@login_required
def class_detail(request, class_id):
    class_instance = get_object_or_404(Class, id=class_id)
    class_students = ClassStudent.objects.filter(class_name=class_instance)

    if request.method == 'POST':
        form = StudentForm(request.POST)
        if form.is_valid():
            roll_no = form.cleaned_data['roll_no']
            
            
            existing_student = Student.objects.filter(roll_no=roll_no).first()

            if existing_student:
                
                if ClassStudent.objects.filter(class_name=class_instance, student=existing_student).exists():
                    messages.warning(request, "Student is already enrolled in this class.")
                else:
                    
                    ClassStudent.objects.create(class_name=class_instance, student=existing_student)
                    messages.success(request, "Student added to the class successfully.")
            else:
                
                student = form.save()
                ClassStudent.objects.create(class_name=class_instance, student=student)
                messages.success(request, "New student added successfully.")

            return redirect('class_detail', class_id=class_id)

    add_student_form = StudentForm()

    return render(request, 'attendance/class_detail.html', {
        'class_instance': class_instance,
        'class_students': class_students,
        'add_student_form': add_student_form
    })


@login_required
def take_attendance(request, class_id):
    class_instance = Class.objects.get(id=class_id)
    class_students = ClassStudent.objects.filter(class_name=class_instance)

    if request.method == 'POST':
        for class_student in class_students:
            present = request.POST.get(f'present_{class_student.id}', 'absent') == 'present'
            Attendance.objects.create(class_student=class_student, present=present)

            if not present:
                student = class_student.student
                student.absences += 1
                student.save()

                if student.absences == 5:
                    teacher_email = class_instance.teacher.email if class_instance.teacher else None  # Ensure the teacher email exists
                    send_absence_email(student, teacher_email, class_instance.name)

        return redirect('class_detail', class_id=class_id)

    return render(request, 'attendance/take_attendance.html', {'class_instance': class_instance, 'class_students': class_students})




def send_absence_email(student, teacher_email, class_name):
    subject = f"Student {student.name} has reached 5 absences in {class_name}"
    
    print(f"Sending email to teacher: {teacher_email}")  
    
    teacher_message = (
        f"Dear Teacher, \n\n"
        f"Student {student.name} has reached 5 absences in your class '{class_name}'. "
        "Please review their attendance and take necessary actions."
    )
    
    guardian_message = (
        f"Dear Guardian, \n\n"
        f"Your child, {student.name}, has reached 5 absences in their class '{class_name}'. "
        "Please contact the school for further information."
    )
    
    from_email = 'sherykhx@gmail.com'
    
    send_mail(subject, teacher_message, from_email, [teacher_email])
    
    if student.guardian_email:
        send_mail(subject, guardian_message, from_email, [student.guardian_email])




@login_required
def attendance_history(request, class_id):
    class_instance = Class.objects.get(id=class_id)
    class_students = ClassStudent.objects.filter(class_name=class_instance)
    return render(request, 'attendance/attendance_history.html', {'class_instance': class_instance, 'class_students': class_students})



@login_required
def edit_student(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    class_student = ClassStudent.objects.filter(student=student).first()
    class_instance = class_student.class_name

    if request.method == 'POST':
        form = EditStudentForm(request.POST, instance=student)  
        if form.is_valid():
            form.save()  
            return redirect('class_detail', class_id=class_instance.id)
        else:
            print("Form Errors:", form.errors)  
    else:
        form = EditStudentForm(instance=student)  

    return render(request, 'attendance/edit_student.html', {
        'form': form,
        'student': student,
        'class_instance': class_instance
    })


@login_required
def attendance_dates(request, class_id):
    class_instance = get_object_or_404(Class, id=class_id)
    attendance_dates = Attendance.objects.filter(class_student__class_name=class_instance).values('date').distinct()

    return render(request, 'attendance/attendance_dates.html', {
        'class_instance': class_instance,
        'attendance_dates': attendance_dates
    })
    
    
    
@login_required
def attendance_records(request, class_id, date):
    class_instance = get_object_or_404(Class, id=class_id)
    attendances = Attendance.objects.filter(class_student__class_name=class_instance, date=date)

    return render(request, 'attendance/attendance_records.html', {
        'class_instance': class_instance,
        'date': date,
        'attendances': attendances
    })
    
    
    
    
def search_attendance(request):
    student_name = request.GET.get('student_name')
    roll_no = request.GET.get('roll_no')  
    subject = request.GET.get('subject')
    filter_type = request.GET.get('filter_type')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    month = request.GET.get('month')
    
    attendance_records = []
    percentage = None

    if student_name and roll_no:  
        try:
            
            student = Student.objects.get(name__icontains=student_name, roll_no=roll_no)
            class_students = ClassStudent.objects.filter(student=student)

            if subject:
                class_students = class_students.filter(class_name__name__icontains=subject)

            if filter_type == 'month' and month:
                try:
                    month_start = datetime.strptime(month, '%B')
                    year = datetime.now().year
                    month_start = month_start.replace(year=year)
                    next_month_start = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1)
                except ValueError:
                    month_start = None

                if month_start:
                    attendances = Attendance.objects.filter(class_student__in=class_students, date__gte=month_start, date__lt=next_month_start)
                else:
                    attendances = Attendance.objects.none()
            else:
                attendances = Attendance.objects.filter(class_student__in=class_students)
                if start_date:
                    attendances = attendances.filter(date__gte=start_date)
                if end_date:
                    attendances = attendances.filter(date__lte=end_date)

            total_days = attendances.count()
            present_days = attendances.filter(present=True).count()
            
            if total_days > 0:
                percentage = (present_days / total_days) * 100

            attendance_records = attendances.order_by('date')
        except Student.DoesNotExist:
            pass

    return render(request, 'attendance/search_results.html', {
        'attendance_records': attendance_records,
        'percentage': percentage,
        'student_name': student_name,
        'roll_no': roll_no,  
    })



def search_results(request):
    
    student_name = request.GET.get('student_name')
    subject = request.GET.get('subject')
    
    if subject:
        attendance_records = Attendance.objects.filter(
            class_student__student__name__icontains=student_name,
            class_student__class_name__name__icontains=subject
        )
    else:
        attendance_records = Attendance.objects.filter(
            class_student__student__name__icontains=student_name
        )
    

    total_classes = attendance_records.count()
    attended_classes = attendance_records.filter(present=True).count()
    percentage = (attended_classes / total_classes * 100) if total_classes else None

    context = {
        'attendance_records': attendance_records,
        'student_name': student_name,
        'subject': subject,
        'percentage': percentage,
    }
    return render(request, 'attendance/search_results.html', context)





@login_required
def generate_report(request, class_id):
    class_instance = get_object_or_404(Class, id=class_id)


    months = list(range(1, 13))  

    if request.method == 'POST':
        student_name = request.POST.get('student_name')
        roll_no = request.POST.get('roll_no')
        
    
        month = int(request.POST.get('month'))
        year = int(request.POST.get('year'))

        class_students = ClassStudent.objects.filter(class_name=class_instance)
        student = class_students.filter(student__name=student_name, student__roll_no=roll_no).first()

        if student:
            
            start_date = date(year, month, 1) 
            end_date = date(year + (1 if month == 12 else 0), (month % 12) + 1, 1)  

            attendances = Attendance.objects.filter(
                class_student=student,
                date__gte=start_date,
                date__lt=end_date
            )
            return generate_pdf(attendances, class_instance, student)

    return render(request, 'attendance/generate_report.html', {
        'class_instance': class_instance,
        'months': months, 
    })


from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER

def generate_pdf(attendances, class_instance, student):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="attendance_report.pdf"'

    # Set up PDF document
    pdf = SimpleDocTemplate(response, pagesize=letter,
                            rightMargin=30, leftMargin=30, topMargin=50, bottomMargin=30)
    elements = []

    
    styles = getSampleStyleSheet()
    
    college_title_style = ParagraphStyle(
        'CollegeTitleStyle',
        fontName='Helvetica-Bold',
        fontSize=18,
        alignment=TA_CENTER,
        spaceAfter=20
    )
    
    title_style = ParagraphStyle(
        'TitleStyle',
        fontName='Helvetica-Bold',
        fontSize=16,
        alignment=TA_CENTER,
        spaceAfter=20
    )

    subtitle_style = ParagraphStyle(
        'SubtitleStyle',
        fontName='Helvetica',
        fontSize=12,
        alignment=TA_CENTER,
        spaceAfter=10
    )


    college_title = Paragraph(
        "FEDERAL GOVT DEGREE COLLEGE FOR MEN PESHAWAR", 
        college_title_style
    )
    elements.append(college_title)


    title = Paragraph(f"<strong>Attendance Report for {student.student.name}</strong>", title_style)
    class_info = Paragraph(f"Class: {class_instance.name}", subtitle_style)
    
    
    elements.append(Spacer(1, 20))
    elements.append(title)
    elements.append(class_info)
    elements.append(Spacer(1, 20))

    
    data = [["Date", "Status"]]
    for attendance in attendances:
        data.append([
            attendance.date.strftime('%Y-%m-%d'), 
            "Present" if attendance.present else "Absent"
        ])


    table = Table(data, colWidths=[3 * inch, 3 * inch])  
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.beige]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 10),
    ]))

    
    elements.append(table)
    pdf.build(elements)

    return response

