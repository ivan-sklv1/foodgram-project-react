from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from users.models import User, Subscribe


admin.site.register(User, UserAdmin)
admin.site.register(Subscribe)
