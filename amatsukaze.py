from network import Network
from utils.live import get_live_url

if __name__ == '__main__':
    network = Network(enable_ipv6=False)
    network.join_network(protocol='ipv4')
    network.play('bilibili', 21790660)
