from django.db import models
from django.utils.translation import gettext_lazy as _

class Server(models.Model):
    PROTOCOL_CHOICES = [
        ('ws', 'WS'),
        ('wss', 'WSS'),
    ]

    url = models.CharField(max_length=255)
    protocol = models.CharField(max_length=3, choices=PROTOCOL_CHOICES)
    user = models.CharField(max_length=100)
    password = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.url} ({self.protocol})"


class Queue(models.Model):
    queue_number = models.CharField(max_length=50, unique=True)
    server = models.ForeignKey(
        Server, 
        on_delete=models.SET_NULL, 
        related_name="queues", 
        null=True, 
        blank=True,
    )

    def __str__(self):
        return self.queue_number


class Extension(models.Model):
    number = models.CharField(max_length=50, unique=True)
    leadvertex_id = models.CharField(max_length=100, blank=True, null=True)
    name = models.CharField(max_length=100, blank=True, null=True)
    queues = models.ManyToManyField(
        Queue, 
        related_name="extensions", 
        blank=True,
    )

    def __str__(self):
        return f"{self.name or 'No Name'} ({self.number})"


class DialStatus(models.Model):
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name or self.code