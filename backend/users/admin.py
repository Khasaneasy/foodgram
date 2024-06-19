from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.db.models import Count

from .models import Profile, Subscribe


class ProfileAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Extra Fields', {'fields': ('avatar',)}),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.annotate(
            recipes_count=Count('recipe'),
            subscribers_count=Count('following__follower')
        )
        return qs

    list_display = UserAdmin.list_display + (
        'recipes_count', 'subscribers_count')


admin.site.register(Profile, UserAdmin)
admin.site.register(Subscribe)
