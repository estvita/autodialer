import requests
from rest_framework import status, viewsets
from rest_framework.response import Response
from ..models import Queue, Extension, DialStatus

from dialer.crm.models import Order, Server

import redis
redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)


class QueueViewSet(viewsets.ViewSet):
    """
    ViewSet для обработки статуса привязки внутреннего номера к очередям.
    """

    def create(self, request):
        """
        Метод для обработки POST-запроса для добавления или удаления номера из очереди.
        """
        internal_number = request.data.get("internal_number")
        queue_number = request.data.get("queue")
        status_action = request.data.get("status")

        # Проверка, что все нужные данные переданы
        if not all([internal_number, queue_number, status_action]):
            return Response({"error": "Недостаточно данных"})
        
        redis_key = f"busy_operators:{internal_number}"
        redis_client.delete(redis_key)

        # Проверка, существует ли очередь
        queue, created = Queue.objects.get_or_create(queue_number=queue_number)

        # Получаем или создаем внутренний номер
        extension, created = Extension.objects.get_or_create(number=internal_number)

        if status_action == "added":
            # Привязываем внутренний номер к очереди
            extension.queues.add(queue)
            return Response({"message": f"Внутренний номер {internal_number} добавлен в очередь {queue_number}."})

        elif status_action == "removed":
            # Отвязываем внутренний номер от очереди
            if queue in extension.queues.all():
                extension.queues.remove(queue)
                return Response({"message": f"Внутренний номер {internal_number} удален из очереди {queue_number}."})
            else:
                return Response({"error": "Внутренний номер не привязан к указанной очереди."})

        else:
            return Response({"error": "Некорректный статус"})


class CallViewSet(viewsets.ViewSet):

    def create(self, request):
        call_id = request.data.get("call_id")
        call_status = request.data.get("call_status")

        if not call_id or not call_status:
            return Response({"error": "call_id and call_status are required"})

        # Получаем или создаем DialStatus
        dialstatus, _ = DialStatus.objects.get_or_create(code=call_status)

        # Формируем ключ для Redis
        redis_key = f"calls:{call_id}"
        if not redis_client.exists(redis_key):
            return Response({"error": f"No record found for call_id {call_id}"})

        # Получаем order_id из Redis
        order_id = redis_client.hget(redis_key, "order_id")
        if not order_id:
            return Response({"error": "Order ID not found in Redis"})

        order_id = int(order_id)

        # Получаем заказ
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return Response({"error": f"Order with ID {order_id} does not exist."})

        order.dial_status = dialstatus

        extension = redis_client.hget(redis_key, "operator")
        if extension:
            extension = extension.decode('utf-8')
        operator = Extension.objects.get(number=extension)
        if operator:
            order.manager = operator

        # Увеличиваем количество звонков
        order.calls = (order.calls or 0) + 1

        operator_key = f"busy_operators:{extension}"

        # Обработка статуса звонка, если он не "ANSWER"
        if call_status != "ANSWER":
            redis_client.delete(operator_key)
            attempts = redis_client.hget(redis_key, "attempts")
            if not attempts:
                return Response({"error": f"Attempts not found in Redis record {redis_key}"})

            attempts = int(attempts)

            # Проверяем, если количество звонков >= attempts
            if order.calls >= attempts:
                next_status_id = redis_client.hget(redis_key, "next_status_id")
                if next_status_id:
                    next_status_id = int(next_status_id)
                    order.calls = 0
                    order.status_id = next_status_id

                    # Изменяем статус в leadvertex
                    lv_server = Server.objects.first()
                    lv_url = f"{lv_server.url}updateOrder.html?token={lv_server.api_key}&id={order_id}"
                    resp = requests.post(lv_url, data={"status": next_status_id})
                    print(f"Ответ от LeadVertex: {resp.status_code}, {resp.text}")

                else:
                    print(f"Поле 'next_status_id' отсутствует в записи {redis_key}.")
        else:
            # ставим оператора на паузу
            pause = redis_client.hget(redis_key, "pause")
            pause = int(pause)
            redis_client.expire(operator_key, pause)

        # Сохраняем изменения в базе данных
        order.save()
        return Response({"message": "Data processed successfully!"})