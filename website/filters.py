from django.utils.translation import gettext_lazy as _
from django.contrib import admin
from django.db.models import Q
from .models import *

class TaskFilter(admin.SimpleListFilter):
    title = _('Has Task')
    parameter_name = 'has_task'

    def lookups(self, request, model_admin):
        return (
            ('True', _('Yes')),
            ('False', _('No')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'True':
            return queryset.exclude(task__exact="")
        elif self.value() == 'False':
            return queryset.filter(Q(task__exact="") | Q(task__isnull=True))


class HasGoogleFilter(admin.SimpleListFilter):
    title = 'Has Google'
    parameter_name = 'has_google'

    def lookups(self, request, model_admin):
        return (
            ('True', 'Yes'),
            ('False', 'No'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'True':
            return queryset.exclude(google__exact='')
        elif self.value() == 'False':
            return queryset.filter(Q(google__exact='') | Q(google__isnull=True))


class HasTheoryFilter(admin.SimpleListFilter):
    title = _('Has Theory')
    parameter_name = 'has_theory'

    def lookups(self, request, model_admin):
        return (
            ('True', _('Yes')),
            ('False', _('No')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'True':
            return queryset.exclude(theory=None)
        elif self.value() == 'False':
            return queryset.filter(theory=None)
        
