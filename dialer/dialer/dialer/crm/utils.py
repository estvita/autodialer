import requests
import redis
from requests.auth import HTTPBasicAuth

from .models import Order, Status

redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)

def is_operator_available(pbx_srv, operator):
    """
    Проверяет доступность номера оператора.
    Возвращает True, если номер доступен, и False, если недоступен.
    """

    redis_key = f"busy_operators:{operator}"
    if redis_client.exists(redis_key):
        return False
    # Проверить DND (Do Not Disturb)
    dnd_url = f'http://{pbx_srv.url}/check-dnd.php?phone={operator}'
    try:
        dnd_resp = requests.get(dnd_url)
        if dnd_resp.text.strip().lower() == 'false':  # Проверяем, что DND равен false

            # Проверить состояние номера на сервере PBX
            endpoint_url = f'http://{pbx_srv.url}:8088/ari/endpoints/pjsip/{operator}'
            resp = requests.get(endpoint_url, auth=HTTPBasicAuth(pbx_srv.user, pbx_srv.password))
            if resp.status_code == 200:
                endpoint_data = resp.json()
                if endpoint_data.get('state') == 'online' and not endpoint_data.get('channel_ids'):
                    return True

    except requests.RequestException as e:
        print(f"Ошибка при проверке доступности номера {operator}: {e}")
    except ValueError:
        print(f"Некорректный ответ от DND-сервиса для номера {operator}")

    return False


def get_order_by_status(status_id, sort_order):
    """
    Получает заказ для заданного статуса, проверяя наличие его ID в Redis.

    :param status_id: ID статуса заказа
    :return: Объект Order или None
    """
    # Получаем заказы для данного статуса
    orders = Order.objects.filter(status_id=status_id).order_by(sort_order)

    if not orders.exists():
        return None

    keys = redis_client.keys("calls:*")

    redis_order_ids = set(
        redis_client.hget(key, "order_id").decode('utf-8') for key in keys if redis_client.hget(key, "order_id")
    )

    # Находим первый заказ, который не присутствует в Redis
    for order in orders:
        if str(order.id) not in redis_order_ids:
            return order

    return None