from utils.login_sites.bilibili import Bilibili


def login(site, username, password):
    cookie = None
    if site == 'bilibili':
        client = Bilibili(username, password)
        cookie = client.cookie()
    return cookie
