import logging as log
import snappi
from datetime import datetime
import time

   
def Test_traffic():
    test_const = {
        "p1_location": "filled_by_user",
        "p2_location": "filled_by_user",
        "pktRate": 200,
        "pktCount": 1000,
        "pktSize": 128,
        "trafficDuration": 20,
        "p1Mac": "0a:ff:d8:c7:9d:0b",
        "p1Ip": "192.168.11.2",
        "p1Gateway": "192.168.11.1",
        "p1Prefix": 24,
        "p2Mac": "0a:ff:c7:75:c5:bf",
        "p2Ip": "192.168.22.2",
        "p2Gateway": "192.168.22.1",
        "p2Prefix": 24,
    }

    api = snappi.api(location="filled_by_user", verify=False)

    c = traffic_config(api, test_const)

    api.set_config(c)

    start_protocols(api)

    # start_capture(api)

    start_transmit(api)

    wait_for(lambda: flow_metrics_ok(api, test_const), "flow metrics",2,90)

    # stop_capture(api)

    # get_capture(api, "p2", "p2.pcap")
    # get_capture(api, "p1", "p1.pcap")


def traffic_config(api, tc):

    c = api.config()
    p1 = c.ports.add(name="p1", location=tc["p1_location"])
    p2 = c.ports.add(name="p2", location=tc["p2_location"])
    
    # capture configuration

    p2_capture = c.captures.add(name="p2_capture")
    p2_capture.set(port_names=["p2"],format="pcap",overwrite=True)
    
    p1_capture = c.captures.add(name="p1_capture")
    p1_capture.set(port_names=["p1"],format="pcap",overwrite=True)

    dp1 = c.devices.add(name="dp1")
    dp2 = c.devices.add(name="dp2")

    dp1_eth = dp1.ethernets.add(name="dp1_eth")
    dp1_eth.connection.port_name = p1.name
    dp1_eth.mac = tc["p1Mac"]
    dp1_eth.mtu = 1500

    dp1_ip = dp1_eth.ipv4_addresses.add(name="dp1_ip")
    dp1_ip.set(address=tc["p1Ip"], gateway=tc["p1Gateway"], prefix=tc["p1Prefix"])


    dp2_eth = dp2.ethernets.add(name="dp2_eth")
    dp2_eth.connection.port_name = p2.name
    dp2_eth.mac = tc["p2Mac"]
    dp2_eth.mtu = 1500

    dp2_ip = dp2_eth.ipv4_addresses.add(name="dp2_ip")
    dp2_ip.set(address=tc["p2Ip"], gateway=tc["p2Gateway"], prefix=tc["p2Prefix"])


    for i in range(0, 2):
        f = c.flows.add()
        f.duration.fixed_packets.packets = tc["pktCount"]
        f.rate.pps = tc["pktRate"]
        f.rate.kbps = tc["pktRate"]
        f.size.fixed = tc["pktSize"]
        f.metrics.enable = True

    fp1_v4 = c.flows[0]
    fp1_v4.name = "fp1_v4"
    fp1_v4.tx_rx.device.set(
        tx_names=[dp1_ip.name], rx_names=[dp2_ip.name]
    )

    fp1_v4_eth, fp1_v4_ip, fp1_v4_tcp = fp1_v4.packet.ethernet().ipv4().tcp()
    fp1_v4_eth.src.value = dp1_eth.mac
    fp1_v4_ip.src.value = tc["p1Ip"]
    fp1_v4_ip.dst.value = tc["p2Ip"]
    fp1_v4_tcp.src_port.value = 5000
    fp1_v4_tcp.dst_port.value = 6000

    fp2_v4 = c.flows[1]
    fp2_v4.name = "fp2_v4"
    fp2_v4.tx_rx.device.set(
        tx_names=[dp2_ip.name], rx_names=[dp1_ip.name]
    )

    fp2_v4_eth, fp2_v4_ip, fp2_v4_tcp = fp2_v4.packet.ethernet().ipv4().tcp()
    fp2_v4_eth.src.value = dp2_eth.mac
    fp2_v4_ip.src.value = tc["p2Ip"]
    fp2_v4_ip.dst.value = tc["p1Ip"]
    fp2_v4_tcp.src_port.value = 5000
    fp2_v4_tcp.dst_port.value = 6000
    
    fp2_v4_tcp.src_port.value = 5000
    fp2_v4_tcp.dst_port.value = 6000

    # print("Config:\n%s", c)
    return c


def flow_metrics_ok(api, tc):
    for m in get_flow_metrics(api):
        if (
            m.transmit != m.STOPPED
            or m.frames_tx != tc["pktCount"]
            or m.frames_rx < tc["pktCount"]
        ):
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

def start_capture(api):
    print("%s Starting capture  ..." % datetime.now())
    cs = api.control_state()
    cs.choice = cs.PORT
    cs.port.choice = cs.port.CAPTURE
    cs.port.capture.set(port_names = [], state="start")
    api.set_control_state(cs)

def stop_capture(api):
    print("%s Stopping capture  ..." % datetime.now())
    cs = api.control_state()
    cs.choice = cs.PORT
    cs.port.choice = cs.port.CAPTURE
    cs.port.capture.set(port_names = [], state="stop")
    api.set_control_state(cs)

def get_capture(api,port_name,file_name):
    print('Fetching capture from port %s' % port_name)
    capture_req = api.capture_request()
    capture_req.port_name = port_name
    pcap = api.get_capture(capture_req)
    with open(file_name, 'wb') as out:
        out.write(pcap.read())

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
