from __future__ import annotations

from django.contrib import admin

from .models import Person


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ("last_name", "first_name", "middle_name", "account_category", "edrpvr_number")
    list_filter = ("account_category",)
    search_fields = ("last_name", "first_name", "middle_name", "edrpvr_number")
