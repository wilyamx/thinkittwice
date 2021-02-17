import datetime
from django.contrib import admin
from django.conf import settings
from django.contrib.auth.hashers import make_password

from easy_select2 import select2_modelform

from PoleLuxe import models

from PoleLuxe.forms import (
    UserForm,
)


class AppAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    search_fields = ['name']


class UserAdmin(admin.ModelAdmin):
    list_max_show_all = 99999
    form = select2_modelform(models.User, {'width': 274}, form_class=UserForm)
    list_filter = [
        'active',
        'django_user__is_staff',
        'django_user__is_superuser',
        'company_id',
        'employment_date',
        'end_date',
    ]
    fields = (
        'username',
        'password',
        'active',
        'email',
        'name',
        'avatar_url',
        'company_id',
        'user_department_id',
        'user_position_id',
        'user_group_id',
        ('employment_date', 'end_date'),
        'is_login',
        'remarks',
    )
    list_display = [
        'id',
        'email',
        'username',
        'active',
        'name',
        'company_id',
        'user_department_id',
        'user_position_id',
        'user_group_id',
        'employment_date',
        'level',
        'points',
        'is_login',
        'access_token',
        'end_date'
    ]
    search_fields = ['email', 'name', 'django_user__email',
                     'django_user__first_name', 'django_user__last_name']
    list_editable = ['is_login']
    actions = ['revoke_token']

    def access_token(self, obj):
        if obj.token:
            return obj.token[:5] + '*' * 27
        return obj.token

    def revoke_token(modeladmin, request, queryset):
        queryset.update(token=None)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        fields = list(self.fields)
        for i, v in enumerate(fields):
            if v == 'password':
                fields[i] = 'new_password'
                break
        self.fields = tuple(fields)

        return super(UserAdmin, self).change_view(
            request, object_id, extra_context=extra_context)

    def manage_end_date(self, obj, form):
        today = datetime.date.today()

        # If the end date has been modified...
        if 'end_date' in form.changed_data:
            # ...to today or in the past, deactivate the user.
            if obj.end_date and obj.end_date <= today:
                obj.active = False

        # If the user is deactivated, set the end date to the current date,
        # but only if the active status has changed, because it's possible
        # that the user is already deactivated (i.e. the active status
        # is unchanged)
        elif not obj.active and 'active' in form.changed_data:
            obj.end_date = today

    def manage_start_date(self, obj, form):
        today = datetime.date.today()

        if 'employment_date' in form.changed_data:
            obj.active = obj.employment_date <= today

    def save_model(self, request, obj, form, change):
        is_new = obj.id is None

        if is_new:
            obj.password = make_password(
                obj.password,
                salt=settings.PASSWORD_SALT
            )

        self.manage_start_date(obj, form)
        self.manage_end_date(obj, form)

        obj.save()


class CompanyOwnerAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'company',
        'owner',
        'created_at'
    ]

    search_fields = [
        'company__name',
        'owner__username'
    ]

    ordering = [
        'company__name',
        'owner__username'
    ]


class CompanyManagerAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'company',
        'manager',
        'created_at'
    ]

    search_fields = [
        'company__name',
        'manager__username'
    ]

    ordering = [
        'company__name',
        'manager__username'
    ]


admin.site.register(models.App, AppAdmin)
admin.site.register(models.User, UserAdmin)
admin.site.register(models.CompanyOwner, CompanyOwnerAdmin)
admin.site.register(models.CompanyManager, CompanyManagerAdmin)
