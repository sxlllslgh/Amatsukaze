import json
import socket
import uuid
from hashlib import sha3_512
from threading import Thread
from time import sleep, time

from utils.ping import ping


class Network:
    __error_ipv4_disabled = 'IPv4 is disabled.'
    __error_ipv6_disabled = 'IPv6 is disabled.'
    __error_announce_data = 'Receive error announce data.'

    def __init__(self, enable_ipv4=True, enable_ipv6=True, port=10129, port6=10129):
        self.__enable_ipv4 = enable_ipv4
        self.__enable_ipv6 = enable_ipv6
        self.__node_id = sha3_512((self.__get_mac() + str(time())).encode('utf8')).hexdigest()
        self.__node_list = []
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

    def create_resource(self):
        pass

    def query_resource(self):
        pass

    def join_group(self):
        pass

    def update_strategy(self):
        pass

    def quit_group(self):
        pass

    @staticmethod
    def __get_mac():
        address = hex(uuid.getnode())[2:]
        return '-'.join(address[i:i + 2] for i in range(0, len(address), 2))

    def __announce_self(self, sock, port):
        addresses = ['<broadcast>'] if self.__node_list == [] else self.__node_list
        while True:
            for address in addresses:
                sock.sendto(('{"type": "announce", "id": %s}' % self.__node_id).encode('utf8'), (address, port))
            sleep(10.0)

    def __echo(self, sock):
        while True:
            data, addr = sock.recvfrom(1024)
            info = json.load(data)
            if 'type' in info.keys():
                if info['type'] == 'announce':
                    try:
                        latency = ping(addr[0])
                        self.__node_list.append((latency, addr, info['id']))
                        self.__node_list.sort(key=lambda node: node[0])
                    except Exception:
                        raise Exception(self.__error_announce_data)
