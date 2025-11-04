import logging as log
import snappi
from datetime import datetime
import time

   
def Test_traffic():
    test_const = {
        "pktRate": 200,
        "pktCount": 12000,
        "pktSize": 128,
        "trafficDuration": 20,
    }

    api = snappi.api(location="https://localhost:8443", verify=False)

    c = traffic_config(api, test_const)

    api.set_config(c)

    start_transmit(api)

    wait_for(lambda: flow_metrics_ok(api, test_const), "flow metrics",2,90)



def traffic_config(api, tc):

    c = api.config()
    p1 = c.ports.add(name="p1", location="localhost:5551")
    p2 = c.ports.add(name="p2", location="10.0.10.12:5551")
    
    for i in range(0, 2):
        f = c.flows.add()
        f.duration.fixed_packets.packets = tc["pktCount"]
        f.rate.pps = tc["pktRate"]
        f.size.fixed = tc["pktSize"]
        f.metrics.enable = True

    fp1 = c.flows[0]
    fp1.name = "fp1"
    fp1.tx_rx.port.set(
        tx_name=p1.name, rx_names=[p2.name]
    )

    fp1_eth, fp1_ip, fp1_tcp = fp1.packet.ethernet().ipv4().tcp()
    fp1_eth.src.value = "12:fe:d0:27:e1:03"
    fp1_eth.dst.value = "12:bd:b6:a9:0e:83"
    fp1_ip.src.value = "10.0.2.12"
    fp1_ip.dst.value = "10.0.2.22"
    fp1_tcp.src_port.value = 5000
    fp1_tcp.dst_port.value = 6000

    fp2 = c.flows[1]
    fp2.name = "fp2"
    fp2.tx_rx.port.set(
        tx_name=p2.name, rx_names=[p1.name]
    )

    fp2_eth, fp2_ip, fp2_tcp = fp2.packet.ethernet().ipv4().tcp()
    fp2_eth.src.value = "12:7d:f7:11:a6:95"
    fp2_eth.dst.value = "12:bd:b6:a9:0e:83"
    fp2_ip.src.value = "10.0.2.22"
    fp2_ip.dst.value = "10.0.2.12"
    fp2_tcp.src_port.value = 5000
    fp2_tcp.dst_port.value = 6000
    
    fp2_tcp.src_port.value = 5000
    fp2_tcp.dst_port.value = 6000

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
