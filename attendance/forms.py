from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Class, Student,ClassStudent

class SignUpForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username','email', 'password1', 'password2']

class ClassForm(forms.ModelForm):
    class Meta:
        model = Class
        fields = ['name','department']

class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['name', 'roll_no', 'guardian_email']


class EditStudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['name', 'roll_no', 'guardian_email']
        
        


class AttendanceReportForm(forms.Form):
    student_name = forms.CharField(max_length=100)
    roll_no = forms.CharField(max_length=20)
    month = forms.ChoiceField(choices=[(i, i) for i in range(1, 13)]) 
    year = forms.IntegerField()
    
    
    
class EnrollStudentForm(forms.ModelForm):
    class Meta:
        model = ClassStudent
        fields = ['class_name', 'student']

    def clean(self):
        cleaned_data = super().clean()
        class_name = cleaned_data.get('class_name')
        student = cleaned_data.get('student')

        # Check if this student is already enrolled in the selected class
        if ClassStudent.objects.filter(class_name=class_name, student=student).exists():
            raise forms.ValidationError(f"{student} is already enrolled in {class_name}")

        return cleaned_data