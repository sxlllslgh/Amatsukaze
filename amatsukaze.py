from dht import DHT


if __name__ == '__main__':
    dht = DHT(enable_ipv6=False)
    dht.join_dht()
