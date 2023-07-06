from django.contrib import admin

from .models import User, Subscription


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'first_name', 'email',)
    list_filter = ('email', 'first_name',)
    empty_value_display = '-пусто-'


admin.site.register(Subscription)
