import requests


def get_live_url(site, room, cookie=None):
    if site == 'bilibili':
        room_url = 'https://api.live.bilibili.com/room/v1/Room/playUrl?cid=%d&qn=0&platform=web' % room
        live_info = requests.get(room_url).json()
        return live_info['data']['durl'][0]['url']