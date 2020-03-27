from os import popen
import re


def ping(addr, count=5):
    latencies = []
    pattern = re.compile(r'=([0-9.]+?)\s?ms')
    ping_result = popen('ping -c %d %s' % (count, addr)).readlines()

    for line in ping_result:
        line_latency = re.search(pattern, line)
        if line_latency:
            latencies.append(float(line_latency.group(1)))

    if len(latencies) == count:
        latencies.pop(0)

    avg_latency = 0.0
    for latency in latencies:
        avg_latency += latency
    avg_latency = avg_latency / len(latencies)

    return avg_latency
