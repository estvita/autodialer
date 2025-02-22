from rest_framework import serializers
from ..models import Order, Status

class CRMOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ["id", "status", "phone"]

    # Поле status будет ссылаться на модель Status через id
    status = serializers.PrimaryKeyRelatedField(queryset=Status.objects.all())
