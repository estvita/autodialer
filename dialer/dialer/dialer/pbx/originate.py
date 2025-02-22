import requests
from dialer.pbx.models import Server

def originate(extension, external, oreder, timeout):

    pbx_srv = Server.objects.first()
    if not pbx_srv:
        print("Ошибка: не найден сервер PBX")
        return "no pbx server"

    payload = {
        'endpoint': f'Local/{external}@from-internal',
        'timeout': timeout,
        'callerId': extension,
        'app': 'thoth.kz',
        'variables': {
            'OPERATOR': str(extension),
            'ORDER': str(oreder)
        }
    }

    resp = requests.post(f'http://{pbx_srv.url}:8088/ari/channels?api_key={pbx_srv.user}:{pbx_srv.password}', json=payload)
    resp_data = resp.json()
    if resp.status_code == 200:
        return resp_data.get('id')
    else:
        return None