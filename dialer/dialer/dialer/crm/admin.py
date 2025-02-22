from django.contrib import admin
from .models import Server, Status, Order
from django.utils.html import format_html

@admin.register(Server)
class ServerAdmin(admin.ModelAdmin):
    list_display = ("url", "api_key")
    search_fields = ("url",)


@admin.register(Status)
class StatusAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)
    readonly_fields = ("id",)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "status", "phone", "calls", "manager", "dial_status", "crm_link")
    search_fields = ("id", "phone")
    list_filter = ("manager", "status", "dial_status")
    list_per_page = 30

    def crm_link(self, obj):
        url = f"https://maximan.leadvertex.ru/admin/order-{obj.id}.html"
        return format_html('<a href="{}" target="_blank">Перейти</a>', url)
