import json
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from .serializers import CRMOrderSerializer
from ..models import Order, Status


class CRMViewSet(viewsets.ViewSet):
    serializer_class = CRMOrderSerializer

    @action(detail=False, methods=["post"])
    def receive(self, request):
        orders = request.data.get("Order", request.data)

        # Если данные - строка, пробуем декодировать как JSON
        if isinstance(orders, str):
            try:
                orders = json.loads(orders)
            except json.JSONDecodeError:
                return Response({"error": "Неверный формат данных JSON"}, status=status.HTTP_200_OK)

        # Если данные - одиночный объект, оборачиваем его в список
        if isinstance(orders, dict):
            orders = [orders]

        if not isinstance(orders, list):
            return Response({"error": "Ожидается список объектов"}, status=status.HTTP_200_OK)

        for item in orders:
            # Получаем или создаем объект Status
            status_obj, created = Status.objects.get_or_create(
                id=item["status"],
                defaults={"name": item["status"]}
            )

            # Создаем или обновляем запись в базе Order
            Order.objects.update_or_create(
                id=item["id"],
                defaults={
                    "status": status_obj,
                    "phone": item["phone"]
                }
            )

        return Response({"message": "Данные получены и обновлены"}, status=status.HTTP_200_OK)
