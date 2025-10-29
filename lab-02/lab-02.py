import logging as log
import snappi
from datetime import datetime
import time

   
def Test_traffic():
    test_const = {
        "lineRatePercentage": 1,
        "mbpsRate": 1,
        "trafficDuration": 60,
        "pktSize": 1500,
        "1Mac": "00:00:01:01:01:01",
        "1Ip": "193.168.11.2",
        "1Gateway": "193.168.11.1",
        "1Prefix": 24,
        "2Mac": "00:00:01:01:02:01",
        "2Ip": "193.168.11.1",
        "2Gateway": "193.168.11.2",
        "2Prefix": 24,
    }

    api = snappi.api(location="https://ixia-c:8443", verify=False)
    c = traffic_test(api, test_const)

    api.set_config(c)
    
    start_protocols(api)
    
    start_transmit(api)
    
    wait_for(lambda: traffic_stopped(api), "traffic stopped",2,500)

    

def traffic_test(api, tc):
    c = api.config()
    p1 = c.ports.add(name="p1", location="eth1")
    p2 = c.ports.add(name="p2", location="eth2")



    d1 = c.devices.add(name="d1")
    d2 = c.devices.add(name="d2")

    d1_eth = d1.ethernets.add(name="d1_eth")
    d1_eth.connection.port_name = p1.name
    d1_eth.mac = tc["1Mac"]
    d1_eth.mtu = 1500

    d1_vlan = d1_eth.vlans.add(name="d1_vlan")
    d1_vlan.set(id=40)
    d1_ip = d1_eth.ipv4_addresses.add(name="d1_ip")
    d1_ip.set(address=tc["1Ip"], gateway=tc["1Gateway"], prefix=tc["1Prefix"])

    d2_eth = d2.ethernets.add(name="d2_eth")
    d2_eth.connection.port_name = p2.name
    d2_eth.mac = tc["2Mac"]
    d2_eth.mtu = 1500
    d2_vlan = d2_eth.vlans.add(name="d2_vlan")
    d2_vlan.set(id=40)

    d2_ip = d2_eth.ipv4_addresses.add(name="d2_ip")
    d2_ip.set(address=tc["2Ip"], gateway=tc["2Gateway"], prefix=tc["2Prefix"])

    f1 = c.flows.add()
    f1.duration.fixed_seconds.seconds = tc["trafficDuration"]
    f1.rate.mbps = tc["mbpsRate"]
    f1.size.fixed = tc["pktSize"]
    f1.metrics.enable = True
    f1.metrics.latency.set(enable=True,mode="cut_through")

    f1.name = "p1_p2"
    f1.tx_rx.port.set(tx_name="p1", rx_name="p2")
    f_eth, f_ip = f1.packet.ethernet().ipv4()
    # f_eth, f_vlan,f_ip = f1.packet.ethernet().vlan().ipv4()
    f_eth.src.value = d1_eth.mac
    f_eth.dst.value = d2_eth.mac
    # f_vlan.id.value = 40
    f_ip.src.value = tc["1Ip"]
    f_ip.dst.value = tc["2Ip"]
    
    f2 = c.flows.add()
    f2.duration.fixed_seconds.seconds = tc["trafficDuration"]
    f2.rate.mbps = tc["mbpsRate"]
    f2.size.fixed = tc["pktSize"]
    f2.metrics.enable = True

    f2.name = "p2_p1"
    f2.tx_rx.port.set(tx_name="p2", rx_name="p1")
    f2_eth, f2_ip = f2.packet.ethernet().ipv4()
    f2_eth.src.value = d2_eth.mac
    f2_eth.dst.value = d1_eth.mac
    f2_ip.src.value = tc["2Ip"]
    f2_ip.dst.value = tc["1Ip"]
    
    return c



def traffic_stopped(api):
    for m in get_flow_metrics(api):
        get_port_metrics(api)
        if m.transmit != m.STOPPED:
            return False
    return True


def get_flow_metrics(api):

    print("%s Getting flow metrics    ..." % datetime.now())
    req = api.metrics_request()
    req.flow.flow_names = []

    metrics = api.get_metrics(req).flow_metrics

    tb = Table(
        "Flow Metrics",
        [
            "Name",
            "State",
            "Frames Tx",
            "Frames Rx",
            "Framerate Tx",
            "Framerate Rx",
            "Bitrate Tx",
            "Bitrate Rx",
            "Bytes Tx",
            "Bytes Rx",
        ],
    )

    for m in metrics:
        tb.append_row(
            [
                m.name,
                m.transmit,
                m.frames_tx,
                m.frames_rx,
                m.frames_tx_rate,
                m.frames_rx_rate,
                m.tx_rate_bps,
                m.rx_rate_bps,
                m.bytes_tx,
                m.bytes_rx,
            ]
        )
    print(tb)
    return metrics


def get_port_metrics(api):

    print("%s Getting port metrics    ..." % datetime.now())
    req = api.metrics_request()
    req.port.port_names = []

    metrics = api.get_metrics(req).port_metrics

    tb = Table(
        "Port Metrics",
        [
            "Name",
            "State",
            "Frames Tx",
            "Frames Rx",
            "FPS Tx",
            "FPS Rx",
            "Bytes Tx",
            "Bytes Rx",
            "Bytes Tx Rate",
            "Bytes Rx Rate",
        ],
    )

    for m in metrics:
        tb.append_row(
            [
                m.name,
                m.transmit,
                m.frames_tx,
                m.frames_rx,
                m.frames_tx_rate,
                m.frames_rx_rate,
                m.bytes_tx,
                m.bytes_rx,
                m.bytes_tx_rate,
                m.bytes_rx_rate,
            ]
        )
    print(tb)
    return metrics


def start_protocols(api):
    print("%s Starting protocols    ..." % datetime.now())
    cs = api.control_state()
    cs.choice = cs.PROTOCOL
    cs.protocol.choice = cs.protocol.ALL
    cs.protocol.all.state = cs.protocol.all.START
    api.set_control_state(cs)


def start_transmit(api):
    print("%s Starting transmit on all flows    ..." % datetime.now())
    cs = api.control_state()
    cs.choice = cs.TRAFFIC
    cs.traffic.choice = cs.traffic.FLOW_TRANSMIT
    cs.traffic.flow_transmit.state = cs.traffic.flow_transmit.START
    api.set_control_state(cs)


def stop_transmit(api):
    print("%s Stopping transmit    ..." % datetime.now())
    cs = api.control_state()
    cs.choice = cs.TRAFFIC
    cs.traffic.choice = cs.traffic.FLOW_TRANSMIT
    cs.traffic.flow_transmit.state = cs.traffic.flow_transmit.STOP
    api.set_control_state(cs)


def wait_for(func, condition_str, interval_seconds=None, timeout_seconds=None):
    """
    Keeps calling the `func` until it returns true or `timeout_seconds` occurs
    every `interval_seconds`. `condition_str` should be a constant string
    implying the actual condition being tested.

    Usage
    -----
    If we wanted to poll for current seconds to be divisible by `n`, we would
    implement something similar to following:
    ```
    import time
    def wait_for_seconds(n, **kwargs):
        condition_str = 'seconds to be divisible by %d' % n

        def condition_satisfied():
            return int(time.time()) % n == 0

        poll_until(condition_satisfied, condition_str, **kwargs)
    ```
    """
    if interval_seconds is None:
        interval_seconds = 1
    if timeout_seconds is None:
        timeout_seconds = 60
    start_seconds = int(time.time())

    print('\n\nWaiting for %s ...' % condition_str)
    while True:
        if func():
            print('Done waiting for %s' % condition_str)
            break
        if (int(time.time()) - start_seconds) >= timeout_seconds:
            msg = 'Time out occurred while waiting for %s' % condition_str
            raise Exception(msg)

        time.sleep(interval_seconds)
    

class Table(object):
    def __init__(self, title, headers, col_width=15):
        self.title = title
        self.headers = headers
        self.col_width = col_width
        self.rows = []

    def append_row(self, row):
        diff = len(self.headers) - len(row)
        for i in range(0, diff):
            row.append("_")

        self.rows.append(row)

    def __str__(self):
        out = ""
        border = "-" * (len(self.headers) * self.col_width)

        out += "\n"
        out += border
        out += "\n%s\n" % self.title
        out += border
        out += "\n"

        for h in self.headers:
            out += ("%%-%ds" % self.col_width) % str(h)
        out += "\n"

        for row in self.rows:
            for r in row:
                out += ("%%-%ds" % self.col_width) % str(r)
            out += "\n"
        out += border
        out += "\n\n"

        return out


if __name__ == "__main__":
    Test_traffic()
