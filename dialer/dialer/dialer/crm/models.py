from django.db import models
from dialer.pbx.models import DialStatus, Extension

class Server(models.Model):
    url = models.URLField()
    api_key = models.CharField(max_length=255)

    def __str__(self):
        return self.url


class Status(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Order(models.Model):
    id = models.IntegerField(primary_key=True)
    status = models.ForeignKey(Status, on_delete=models.SET_NULL, null=True, related_name="orders")
    dial_status = models.ForeignKey(DialStatus, on_delete=models.SET_NULL, null=True, blank=True)
    manager = models.ForeignKey(
        Extension, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="orders", 
    )
    phone = models.CharField(max_length=15)
    calls = models.IntegerField(default=0, null=True, blank=True)

    def __str__(self):
        return f"Order {self.id} - {self.phone}"