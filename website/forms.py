from django import forms
from .models import *
from django.contrib.auth import get_user_model


### Admin
class StudyPlanForm(forms.Form):
    users = forms.ModelMultipleChoiceField(queryset=User.objects.exclude(teacher=True), required=False)
    groups = forms.ModelMultipleChoiceField(queryset=Group.objects.all(), required=False)
    theories = forms.ModelMultipleChoiceField(queryset=Theory.objects.all().order_by("topic__order", "order"), required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['groups'].label = "Группы"
        self.fields['users'].label = "Ученики"
        self.fields['theories'].label = "Темы"

    def save(self):
        users = self.cleaned_data['users']
        groups = self.cleaned_data['groups']
        theories = self.cleaned_data['theories'].distinct()
        for group in groups:
            for user in group.users.all():
                for theory in theories:
                    StudyPlan.objects.get_or_create(user=user, title=theory)
        for user in users:
            for theory in theories:
                StudyPlan.objects.get_or_create(user=user, title=theory)


class GetStudyPlan(forms.Form):
    users_show = forms.ModelChoiceField(queryset=User.objects.exclude(teacher=True))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.label = False


### Teachers
class StudyPlanFormTeacher(forms.Form):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super().__init__(*args, **kwargs)
        students = user.teacher_students.all().values_list('students__username', flat=True)
        groups = user.teacher_students.all().values_list('groups', flat=True)
        self.fields['users'] = forms.ModelMultipleChoiceField(queryset=User.objects.filter(username__in=students), required=False)
        self.fields['groups'] = forms.ModelMultipleChoiceField(queryset=Group.objects.filter(pk__in=groups), required=False)
        self.fields['theories'] = forms.ModelMultipleChoiceField(queryset=Theory.objects.all().order_by("topic__order", "order"), required=False)
        
        # Labels
        self.fields['groups'].label = "Группы"
        self.fields['users'].label = "Ученики"
        self.fields['theories'].label = "Темы"

    def save(self):
        users = self.cleaned_data['users']
        groups = self.cleaned_data['groups']
        theories = self.cleaned_data['theories'].distinct()
        for group in groups:
            for user in group.users.all():
                for theory in theories:
                    StudyPlan.objects.get_or_create(user=user, title=theory)
        for user in users:
            for theory in theories:
                StudyPlan.objects.get_or_create(user=user, title=theory)


class GetStudyPlanTeacher(forms.Form):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super().__init__(*args, **kwargs)
        students = user.teacher_students.all().values_list('students__username', flat=True)
        self.fields['users_show_teacher'] = forms.ModelChoiceField(queryset=User.objects.filter(username__in=students))
        for field in self.fields.values():
            field.label = False


### Dictionary
class WordFilterForm(forms.Form):
    topics = forms.ModelChoiceField(
        queryset=Topic.objects.all(),
        widget=forms.Select,
        required=False,
        empty_label="No Topic",
        initial=0,
    )
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['topics'].choices = [(0, 'All Words')] + list(self.fields['topics'].choices)


### for users
class WordFilterFormUser(forms.Form):
    
    topics = forms.ModelChoiceField(
        queryset=Topic.objects.all(),
        widget=forms.Select,
        required=False,
        empty_label="No topic",
        initial=0, # Set the default value to the "All Words" option
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['topics'].queryset = Topic.objects.filter(words__userwords__user=user).distinct()

        # Add the custom option to choices
        self.fields['topics'].choices = [(0, 'All Words')] + list(self.fields['topics'].choices)


class ContribFilterForm(forms.Form):
    contributor = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(words__isnull=False).distinct(),
        widget=forms.SelectMultiple,
        required=False,
    )