import logging as log
import snappi
from datetime import datetime
import time

   
def Test_traffic():
    test_const = {
        "p1_location": "eth1",
        "p2_location": "eth2",
        "p3_location": "eth3",
        "lineRatePercentage": 1,
        "rate": 100,
        "trafficDuration": 60,
        "pktSize": 500,
        "p1Mac": "00:00:01:01:01:01",
        "p1Ip": "193.168.11.2",
        "p2Mac": "00:00:01:01:02:01",
        "p2Ip": "193.168.22.1",
        "p3Mac": "00:00:01:01:03:01",
        "p3Ip": "193.168.22.2",
    }

    api = snappi.api(location="https://ixia-c:8443", verify=False)
    c = traffic_test(api, test_const)

    api.set_config(c)
    
    start_transmit(api)
    
    wait_for(lambda: traffic_stopped(api), "traffic stopped",2,500)

    

def traffic_test(api, tc):
    c = api.config()
    c.ports.add(name="p1", location=tc["p1_location"])
    c.ports.add(name="p2", location=tc["p2_location"])
    c.ports.add(name="p3", location=tc["p3_location"])

    portList = ["p1", "p2", "p3"]
    for src in portList:
        for dst in portList:
            if src != dst:
                f = c.flows.add()
                f.duration.fixed_seconds.seconds = tc["trafficDuration"]
                f.rate.kbps = tc["rate"]
                f.size.fixed = tc["pktSize"]
                f.metrics.enable = True

                f.name = "%s_to_%s" % (src, dst)
                f.tx_rx.port.set(tx_name=src, rx_names=[dst])

                f_eth, f_ip = f.packet.ethernet().ipv4()
                f_eth.src.value = tc["%sMac" % src]
                f_eth.dst.value = tc["%sMac" % dst]
                f_ip.src.value = tc["%sIp" % src]
                f_ip.dst.value = tc["%sIp" % dst]
                
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
    # print(tb)
    return metrics


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
