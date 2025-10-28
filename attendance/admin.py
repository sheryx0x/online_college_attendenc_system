from django.contrib import admin
from .models import Student,Teacher,Class,ClassStudent,Attendance,Department



admin.site.register(Department)
admin.site.register(Student)
admin.site.register(Teacher)
admin.site.register(Class)
admin.site.register(ClassStudent)
admin.site.register(Attendance)