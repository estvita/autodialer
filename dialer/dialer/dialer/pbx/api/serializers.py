from rest_framework import serializers
from ..models import Queue, Extension

class QueueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Queue
        fields = ['id', 'queue_number']

class ExtensionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Extension
        fields = ['id', 'number', 'queue']
