from django.db import models
from django.contrib.auth.models import User

class Student(models.Model):
    name = models.CharField(max_length=100)
    roll_no = models.CharField(max_length=20)
    absences = models.IntegerField(default=0)
    guardian_email = models.EmailField(max_length=254, blank=True, null=True)
    def __str__(self):
        return f"{self.name} ({self.roll_no})"

class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=254, default='default@example.com')

    def __str__(self):
        return self.name
    
    
    
class Department(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Class(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, null=True)  
    name = models.CharField(max_length=100)
    students = models.ManyToManyField(Student, through='ClassStudent')

    def __str__(self):
        return self.name



class ClassStudent(models.Model):
    class_name = models.ForeignKey(Class, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    class Meta:
        unique_together = ('class_name', 'student')

class Attendance(models.Model):
    class_student = models.ForeignKey(ClassStudent, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    present = models.BooleanField(default=False)
