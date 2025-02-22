from django.contrib import admin
from .models import Queue, Extension, Server, DialStatus

@admin.register(Server)
class ServerAdmin(admin.ModelAdmin):
    list_display = ("url", "protocol", "user")
    search_fields = ("url", "user")


@admin.register(Queue)
class QueueAdmin(admin.ModelAdmin):
    list_display = ("queue_number", "server")
    search_fields = ("queue_number",)


@admin.register(Extension)
class ExtensionAdmin(admin.ModelAdmin):
    list_display = ("number", "leadvertex_id", "name")
    # filter_horizontal = ('queues',)  
    search_fields = ("number",)
    readonly_fields = ("number", 'queues')

@admin.register(DialStatus)
class DialStatusAdmin(admin.ModelAdmin):
    list_display = ("code", "name")
    search_fields = ("code", "name")
    readonly_fields = ("code", )