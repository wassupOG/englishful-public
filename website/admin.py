from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.admin import RelatedOnlyFieldListFilter
from django.contrib.auth.hashers import make_password
from .models import *
from .forms import *
from .filters import *

# Register your models here.
class CustomUserAdmin(BaseUserAdmin):
    list_display = ('username', 'first_name', 'last_name', 'cefr', 'progress', 'comment')
    
    # specify the fields to be displayed in the detail view
    list_filter = ('cefr', 'teacher', HasGoogleFilter)
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('teacher', 'first_name', 'last_name', 'email', 'comment', 'cefr', 'progress', 'gpa', 'google')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    def save_model(self, request, obj, form, change):
        # Check if password has been changed
        if 'password' in form.changed_data:
            obj.password = make_password(form.cleaned_data['password'])
        super().save_model(request, obj, form, change)


class StudyPlanAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'grade', 'covered')
    list_filter = (('user', RelatedOnlyFieldListFilter), 'covered')
    ordering = ('-title', )


class ResultsAdmin(admin.ModelAdmin):
    list_filter = (
        ('user', RelatedOnlyFieldListFilter),
        ('test_proper__topic', admin.RelatedOnlyFieldListFilter),
    )
    list_display = ('user', 'test_proper_topic', 'test_proper_theory', 'test_proper_testname', 'date', 'grade')

    def test_proper_topic(self, obj):
        return obj.test_proper.topic
    test_proper_topic.short_description = 'Topic'
    test_proper_topic.admin_order_field = 'test_proper__topic'

    def test_proper_theory(self, obj):
        return obj.test_proper.theory
    test_proper_theory.short_description = 'Theory'
    test_proper_theory.admin_order_field = 'test_proper__theory'

    def test_proper_testname(self, obj):
        return obj.test_proper.testname
    test_proper_testname.short_description = 'Test Name'
    test_proper_testname.admin_order_field = 'test_proper__testname'


class EGEresultsAdmin(admin.ModelAdmin):
    list_filter = ('test_proper', 'checked', 'speaking_audio')
    list_display = ('test_proper', 'user', 'checked', 'speaking_audio', 'converted_score', 'raw')


class TheoryAdmin(admin.ModelAdmin):
    list_display = ('topic', 'title', 'cefr', 'order')
    list_filter = (('topic', RelatedOnlyFieldListFilter), 'cefr')
    ordering = ('-topic', )


class TheoryTopicsAdmin(admin.ModelAdmin):
    ordering = ['order']


class TestsAdmin(admin.ModelAdmin):
    list_display = ('testname', 'theory', 'order', 'topic', 'lvl', 'type')
    list_filter = (('topic', RelatedOnlyFieldListFilter), 'lvl', ('type', RelatedOnlyFieldListFilter), TaskFilter, HasTheoryFilter, 'case')
    ordering = ('topic', 'order')


class TeacherStudentAdmin(admin.ModelAdmin):
    list_filter = ('teacher', )
    filter_horizontal = ('students', 'groups')
    fields = ('teacher', 'students', 'groups')  # add the groups field to the form

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        obj = form.instance

        # Add users from groups to the students field of the related TeacherStudent object
        for group in obj.groups.all():
            obj.students.add(*group.users.all())

        # Remove users from groups that were removed from the TeacherStudent object
        removed_groups = [group for group in form.initial.get('groups', []) if group not in form.cleaned_data.get('groups', [])]
        for group in removed_groups:
            obj.students.remove(*group.users.all())


class GroupAdmin(admin.ModelAdmin):
    filter_horizontal = ('users',)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        obj = form.instance

        # Add users from this group to the students field of related TeacherStudent objects
        for teacher_student in TeacherStudent.objects.filter(groups=obj):
            teacher_student.students.add(*obj.users.filter(teacher=False))
        
        # Remove users that were removed from the group from the students field of related TeacherStudent objects
        initial_users = form.initial.get('users', [])
        current_users = form.cleaned_data.get('users', [])
        removed_users = [user for user in initial_users if user not in current_users]

        if removed_users:
            for teacher_student in TeacherStudent.objects.filter(groups=obj):
                teacher_student.students.remove(*removed_users)
                
                # Delete TeacherStudent object if it has no students left
                if teacher_student.students.count() == 0:
                    teacher_student.delete()


class ReviewsAdmin(admin.ModelAdmin):
    list_display = ('user', 'service', 'img', 'social')


class UserWordsAdmin(admin.ModelAdmin):
    list_filter = ('user',)


class EGEtestsAdmin(admin.ModelAdmin):
    list_filter = ('ege_testname', )


admin.site.register(User, CustomUserAdmin)
admin.site.register(Results, ResultsAdmin)
admin.site.register(Words)
admin.site.register(UserWords, UserWordsAdmin)
admin.site.register(Topic)
admin.site.register(Theory, TheoryAdmin)
admin.site.register(TheoryTopics, TheoryTopicsAdmin)
admin.site.register(EGEresults, EGEresultsAdmin)
admin.site.register(StudyPlan, StudyPlanAdmin)
admin.site.register(Tests, TestsAdmin)
admin.site.register(FreeTests)
admin.site.register(Posts)
admin.site.register(TestTypes)
admin.site.register(TeacherStudent, TeacherStudentAdmin)
admin.site.register(Group, GroupAdmin)
admin.site.register(Reviews, ReviewsAdmin)
admin.site.register(EGEtests, EGEtestsAdmin)