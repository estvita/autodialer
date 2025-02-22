import configparser
import websocket
import redis
import json
import time
import requests
import logging

# Настройка логгера
LOG_FILE = "events.log"
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


websocket.enableTrace(False)

config = configparser.ConfigParser()
config.read('config.ini')

WS_TYPE = config.get('asterisk', 'ws_type')
HOST = config.get('asterisk', 'host')
PORT = config.get('asterisk', 'port')
USER = config.get('asterisk', 'username')
SECRET = config.get('asterisk', 'secret')
CRM_URL = config.get('crm', 'domain')
BASE_URL = f'http://{HOST}:{PORT}/ari'
API_KEY = f'api_key={USER}:{SECRET}'

DIALER_URL = config.get('dialer', 'url')
DIALER_KEY = config.get('dialer', 'api-key')

redis_client = redis.StrictRedis(host='localhost', port=6379, decode_responses=True)


def get_channel_id_by_name(channel_name):
    """
    Получает channel_id из Redis по известному channel_name.
    """
    keys = redis_client.keys("dialer:*")
    for key in keys:
        stored_channel_name = redis_client.hget(key, 'CHANNEL')
        if stored_channel_name and stored_channel_name == channel_name:
            return key.split(':')[1]
    return None


def finish_call(channel_id, status):

    payload = {
        'call_id': channel_id,
        'call_status': status
    }
    resp = requests.post(f'{DIALER_URL}call/?api-key={DIALER_KEY}', json=payload)
    print('Dialer answer', resp.json())


def on_message(ws, message):
    event = json.loads(message)
    event_type = event.get('type')
    channel = event.get('channel', {})
    channel_name = channel.get('name')
    if channel_name:
        channel_name = channel_name.split(';')[0]
    channel_id = channel.get('id')
    redis_key = f"dialer:{channel_id}"

    if event_type not in ['ChannelVarset', 'ChannelDialplan']:
        logging.info(json.dumps(event))

    if event_type == 'ChannelCreated':
        state = channel.get('state')
        if state not in ['Down']:
            return
        dialplan = channel.get('dialplan', {})
        context = dialplan.get('context')
        if context not in ['from-internal']:
            return
        redis_client.hset(redis_key, 'CHANNEL', channel_name)
        redis_client.expire(redis_key, 3600)
    
    elif event_type == 'ChannelVarset':
        stored_channel_id = get_channel_id_by_name(channel_name)
        if stored_channel_id != channel_id:
            return
        variable = event.get('variable')
        if variable in ['OPERATOR', 'ORDER']:
            value = event.get('value')
            redis_client.hset(redis_key, variable, value)
    
    elif event_type == 'StasisStart':
        operator = redis_client.hget(redis_key, 'OPERATOR')
        if not operator:
            return

        dial_url = f'{BASE_URL}/channels/{channel_id}/continue?{API_KEY}'
        payload = {
            'context': 'from-internal',
            'extension': operator,
            'priority': 1
        }
        response = requests.post(dial_url, json=payload)
        print(f"Перенаправление выполнено. Код ответа: {response.status_code}")
    
    elif event_type == 'ChannelEnteredBridge':
        if not redis_client.exists(redis_key):
            return
        connected = channel.get('connected', {})
        exten = connected.get('number')
        order = redis_client.hget(redis_key, 'ORDER')
        if not order:
            return
        caller = channel.get('caller', {})
        caller_num = caller.get('number')

        payload = {
            'from': caller_num,
            'body': f'https://{CRM_URL}/operator/order-{order}.html'
        }
        msg_url = f'{BASE_URL}/endpoints/pjsip/{exten}/sendMessage?{API_KEY}'
        response = requests.put(msg_url, json=payload)


    elif event_type == 'Dial':        

        dialstatus = event.get('dialstatus')
        if not dialstatus or dialstatus in ['RINGING', 'PROGRESS']:
            return
        
        caller_or_peer = event.get('caller') or event.get('peer')
        channel_name = caller_or_peer.get('name', '').split(';')[0]
        stored_channel_id = get_channel_id_by_name(channel_name)
        if not stored_channel_id:
            return
        redis_key = f"dialer:{stored_channel_id}"
        redis_client.hset(redis_key, 'STATUS', dialstatus)
        
        if dialstatus in ['CHANUNAVAIL', 'NOANSWER']:
            if not redis_client.exists(redis_key):
                return
            redis_client.delete(redis_key)
            hangup_url = f'{BASE_URL}/channels/{channel_id}?{API_KEY}'
            response = requests.delete(hangup_url)

            finish_call(stored_channel_id, dialstatus)
    
    elif event_type == 'ChannelDestroyed':
        stored_channel_id = get_channel_id_by_name(channel_name)
        if not stored_channel_id:
            return
        
        redis_key = f"dialer:{stored_channel_id}"

        if redis_client.exists(redis_key):
            dialstatus = redis_client.hget(redis_key, 'STATUS')
            if not dialstatus:
                return
            redis_client.delete(redis_key)
            finish_call(stored_channel_id, dialstatus)
        

def on_error(ws, error):
    print("Error:", error)

def on_close(ws):
    print("### closed ###")

def on_open(ws):
    print("Opened connection")

def run_websocket():
    while True:
        ws = websocket.WebSocketApp(f"{WS_TYPE}://{HOST}:{PORT}/ari/events?{API_KEY}&app=thoth.kz&subscribeAll=true",
                                    on_message=on_message,
                                    on_error=on_error)
        ws.on_open = on_open
        ws.run_forever(ping_interval=60, ping_timeout=10)
        print("Reconnecting...")
        time.sleep(1)


if __name__ == '__main__':
    run_websocket()
