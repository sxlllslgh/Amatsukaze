import json
import socket
import uuid
from bisect import insort_left
from hashlib import sha3_512
from threading import Thread
from time import sleep, time

import requests

from utils.live import get_live_url
from utils.ping import ping


class Network:
    __error_ipv4_disabled = 'IPv4 is disabled.'
    __error_ipv6_disabled = 'IPv6 is disabled.'
    __error_announce_data = 'Receive error announce data.'
    __error_node_info_data = 'Receive error node information.'
    __error_unexpected_echo = 'Receive unexpected resource echo.'
    __error_no_resource = 'Resource requested does not exist.'

    def __init__(self, enable_ipv4=True, enable_ipv6=True, port=10129, port6=10129):
        self.__enable_ipv4 = enable_ipv4
        self.__enable_ipv6 = enable_ipv6
        self.__node_id = sha3_512((self.__get_mac() + str(time())).encode('utf8')).hexdigest()
        self.__node_list = []
        self.__groups = dict()
        if self.__enable_ipv4:
            self.__communication_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.__communication_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self.__communication_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.__communication_socket.bind(('', port))
            self.__communication_announce_thread = Thread(target=Network.__announce_self,
                                                          args=(self, self.__communication_socket, port), daemon=True)
            self.__communication_echo_thread = Thread(target=Network.__echo, args=(self, self.__communication_socket),
                                                      daemon=True)
        if self.__enable_ipv6:
            self.__communication_socket6 = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
            self.__communication_socket6.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self.__communication_socket6.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.__communication_socket6.bind(('', port6))
            self.__communication_announce6_thread = Thread(target=Network.__announce_self,
                                                           args=(self, self.__communication_socket6, port6),
                                                           daemon=True)
            self.__communication_echo6_thread = Thread(target=Network.__echo, args=(self, self.__communication_socket6),
                                                       daemon=True)

    def join_network(self, protocol='both'):
        ipv4 = False if protocol == 'ipv6' else True
        ipv6 = False if protocol == 'ipv4' else True
        if ipv4:
            if self.__enable_ipv4:
                self.__communication_announce_thread.start()
                self.__communication_echo_thread.start()
            else:
                raise Exception(self.__error_ipv4_disabled)
        if ipv6:
            if self.__enable_ipv6:
                self.__communication_announce6_thread.start()
                self.__communication_echo6_thread.start()
            else:
                raise Exception(self.__error_ipv6_disabled)

    def create_resource(self, site, room, username, password, ipv4_download=0.0, ipv4_upload=0.0, ipv6_download=0.0,
                        ipv6_upload=0.0):
        # cookie = login(site, username, password)
        resource_id = sha3_512((site + str(room)).encode('utf8')).hexdigest()
        self.__groups[resource_id] = {
            'cookie': None,
            'url': get_live_url(site, room),
            'strategy': {
                'ipv4': {
                    'download': ipv4_download,
                    'upload': ipv4_upload
                },
                'ipv6': {
                    'download': ipv6_download,
                    'upload': ipv6_upload
                }
            },
            'nodes': []
        }
        self.__query_resource(resource_id)
        sleep(self.__node_list[-1][0] * 3000.0)

    def play(self, site, room, ipv4_download=0.0, ipv4_upload=0.0, ipv6_download=0.0, ipv6_upload=0.0):
        resource_id = sha3_512((site + str(room)).encode('utf8')).hexdigest()
        if resource_id not in self.__groups:
            self.create_resource(site, room, ipv4_download, ipv4_upload, ipv6_download, ipv6_upload)
        self.__play_stream(resource_id)

    def update_strategy(self, site, room, protocol, direction, limit):
        resource_id = sha3_512((site + str(room)).encode('utf8')).hexdigest()
        if resource_id in self.__groups:
            self.__groups[resource_id][protocol][direction] = limit
        else:
            raise Exception(self.__error_no_resource)

    def quit_group(self, site, room):
        resource_id = sha3_512((site + str(room)).encode('utf8')).hexdigest()
        for node in self.__groups[resource_id]['nodes']:
            self.__communication_socket.sendto(
                ('{"type": "quit", "id": "%s", "node_id": "%s"}' % (resource_id, self.__node_id)).encode('utf8'),
                node['addr'])

    @staticmethod
    def __get_mac():
        address = hex(uuid.getnode())[2:]
        return '-'.join(address[i:i + 2] for i in range(0, len(address), 2))

    def __announce_self(self, sock, port):
        addresses = ['<broadcast>'] if self.__node_list == [] else self.__node_list
        while True:
            for address in addresses:
                sock.sendto(('{"type": "announce", "id": "%s"}' % self.__node_id).encode('utf8'), (address, port))
            sleep(10.0)

    def __echo(self, sock):
        while True:
            data, addr = sock.recvfrom(1024)
            info = json.load(data)
            if 'type' in info.keys():
                if info['type'] == 'announce':
                    try:
                        Thread(target=Network.__add_node, args=(self, info['id'], addr), daemon=True).start()
                        for node in self.__node_list:
                            sock.sendto(('{"type": "node_info", "id": "%s", "addr": "%s", "port": %d}' % (
                                node['id'], node['addr'][0], node['addr'][1])).encode('utf8'), addr)
                    except Exception:
                        raise Exception(self.__error_announce_data)
                elif info['type'] == 'node_info':
                    Thread(target=Network.__add_node, args=(self, info['id'], (info['addr'], info['port'])),
                           daemon=True).start()
                elif info['type'] == 'query_resource':
                    if info['id'] in self.__groups:
                        sock.sendto(('{"type": "echo_resource", "id": "%s", "node_id": "%s"}' % (
                        info['id'], self.__node_id)).encode('utf8'), addr)
                elif info['type'] == 'echo_resource':
                    try:
                        self.__groups[info['id']].append(info['node_id'])
                    except Exception:
                        raise Exception(self.__error_unexpected_echo)
                elif info['type'] == 'quit':
                    if info['id'] in self.__groups:
                        if info['node_id'] in self.__groups[info['id']]['nodes']:
                            del self.__groups[info['id']]['nodes'][info['node_id']]

    def __add_node(self, node_id, addr):
        try:
            latency = ping(addr[0])
            insort_left(self.__node_list, (latency, addr, node_id))
        except Exception:
            raise Exception(self.__error_node_info_data)

    @staticmethod
    def __ask_node(sock, addr, resource_id):
        sock.sendto(('{"type": "query_resource", "id": "%s"}' % resource_id).encode('utf8'), addr)

    def __query_resource(self, resource_id):
        for node in self.__node_list:
            Thread(target=Network.__ask_node, args=(self.__communication_socket, node[1], resource_id),
                   daemon=True).start()

    def __play_stream(self, resource_id):
        response = requests.get(self.__groups[resource_id]['url'], headers={'Referer': 'https://live.bilibili.com', }, stream=True, verify=False)
