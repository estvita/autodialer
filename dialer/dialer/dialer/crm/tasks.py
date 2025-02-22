from celery import shared_task
import redis

import dialer.crm.utils as utils
from dialer.pbx.models import Queue, Server

from dialer.pbx.originate import originate

redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)

@shared_task()
def call_task(queue_id: int,
              dial_status_id: int,
              next_status_id: int,
              attempts: int,
              interval: int,
              timeout: int,
              pause: int,
              sort_order: str):
    """
    Основная задача для обработки обзвона.
    """
    pbx_srv = Server.objects.first()
    if not pbx_srv:
        print("Ошибка: не найден сервер PBX")
        return "no pbx server"

    try:
        queue = Queue.objects.get(queue_number=queue_id)
    except Queue.DoesNotExist:
        print(f"Очередь с номером {queue_id} не найдена")
        return "queue not found"

    # Запрашиваем актуальные данные операторов
    extensions = queue.extensions.all()
    extension_numbers = [ext.number for ext in extensions]

    # Проверяем доступность номеров
    for operator in extension_numbers:
        if utils.is_operator_available(pbx_srv, operator):
            order = utils.get_order_by_status(dial_status_id, sort_order)
            if order:
                call_id = originate(operator, order.phone, order.id, timeout)
                if call_id:
                    redis_key = f"busy_operators:{operator}"
                    redis_client.set(redis_key, "reserved", ex=interval)
                    redis_key = f"calls:{call_id}"
                    redis_client.hset(redis_key, mapping={
                        "order_id": order.id,
                        "operator": operator,
                        "pause": pause,
                        "next_status_id": next_status_id,
                        "attempts": attempts,
                    })
                    redis_client.expire(redis_key, interval)
                    return f"call for {order.id}. call_id: {call_id}"

    return f"call not possible {queue_id}."