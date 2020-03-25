from threading import Thread
import socket
from time import sleep, time


class DHT:
    def __init__(self, command='Find Amatsukaze Nodes.', enable_ipv4=True, enable_ipv6=True, port=10129, port6=10129):
        self.__communication_command = bytes(command, encoding='utf8')
        self.__enable_ipv4 = enable_ipv4
        self.__enable_ipv6 = enable_ipv6
        self.__node_list = dict()
        self.__node_clear_thread = Thread(target=DHT.__clear_nodes, daemon=True)
        if self.__enable_ipv4:
            self.__communication_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.__communication_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self.__communication_listen_thread = Thread(target=DHT.__listen_nodes, args=(self, self.__communication_socket), daemon=True)
            self.__communication_send_thread = Thread(target=DHT.__send_self, args=(self, self.__communication_socket, port), daemon=True)
        if self.__enable_ipv6:
            self.__enable_ipv6 = True
            self.__communication_socket6 = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
            self.__communication_socket6.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self.__communication_listen_thread6 = Thread(target=DHT.__listen_nodes, args=(self, self.__communication_socket6), daemon=True)
            self.__communication_send_thread6 = Thread(target=DHT.__send_self, args=(self, self.__communication_socket6, port), daemon=True)

    def join_dht(self):
        if self.__enable_ipv4:
            self.__communication_listen_thread.start()
            self.__communication_send_thread.start()
        if self.__enable_ipv6:
            self.__communication_listen_thread6.start()
            self.__communication_send_thread6.start()
        self.__node_clear_thread.start()

    def __send_self(self, sock, port):
        while True:
            sock.bind(('', port))
            sock.sendto(self.__communication_command, ('<broadcast>', port))
            sleep(10.0)

    def __listen_nodes(self, sock):
        while True:
            data, addr = sock.recvfrom(len(self.__communication_command))
            if data == self.__communication_command:
                self.__node_list[addr] = time()

    def __clear_nodes(self):
        while True:
            self.__node_list = {addr: last_announce for addr, last_announce in self.__node_list.items() if time() - last_announce > 300.0}
            sleep(300.0)