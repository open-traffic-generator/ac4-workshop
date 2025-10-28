import logging as log
import snappi
from datetime import datetime
import time

   
def Test_ebgp_route_prefix():
    test_const = {
        "pktRate": 200,
        "pktCount": 1000,
        "pktSize": 128,
        "trafficDuration": 20,
        "p1Mac": "0a:ff:d8:c7:9d:0b",
        "p1Ip": "10.0.2.22",
        "p1Gateway": "10.0.2.1",
        "p1Prefix": 24,
        "p1As": 1111,
        "p2Mac": "0a:ff:c7:75:c5:bf",
        "p2Ip": "10.0.2.12",
        "p2Gateway": "10.0.2.1",
        "p2Prefix": 24,
        "p2As": 1112,
        "p1RouteCount": 5,
        "p2RouteCount": 5,
        "p1NextHopV4": "1.1.1.3",
        "p1NextHopV6": "::1:1:1:3",
        "p2NextHopV4": "1.1.1.4",
        "p2NextHopV6": "::1:1:1:4",
        "p1AdvRouteV4": "10.10.10.1",
        "p2AdvRouteV4": "20.20.20.1",
        "p1AdvRouteV6": "::10:10:10:1",
        "p2AdvRouteV6": "::20:20:20:1",
    }

    api = snappi.api(location="https://localhost:8443", verify=False)

    c = ebgp_route_prefix_config(api, test_const)

    api.set_config(c)

    start_protocols(api)

    wait_for(lambda: bgp_metrics_ok(api, test_const),"correct bgp peering")

    wait_for(lambda: bgp_prefixes_ok(api, test_const),"correct bgp prefixes")

    # start_capture(api)

    start_transmit(api)

    wait_for(lambda: flow_metrics_ok(api, test_const), "flow metrics",2,90)

    # stop_capture(api)

    # get_capture(api, "p2", "p2.pcap")
    # get_capture(api, "p1", "p1.pcap")


def ebgp_route_prefix_config(api, tc):
    c = api.config()
    p1 = c.ports.add(name="p1", location="localhost:5551+localhost:50071")
    p2 = c.ports.add(name="p2", location="10.24.50.227:5551+10.24.50.227:50071")
    
    # capture configuration

    p2_capture = c.captures.add(name="p2_capture")
    p2_capture.set(port_names=["p2"],format="pcap",overwrite=True)
    
    p1_capture = c.captures.add(name="p1_capture")
    p1_capture.set(port_names=["p1"],format="pcap",overwrite=True)

    d1 = c.devices.add(name="d1")
    d2 = c.devices.add(name="d2")

    d1_eth = d1.ethernets.add(name="d1_eth")
    d1_eth.connection.port_name = p1.name
    d1_eth.mac = tc["p1Mac"]
    d1_eth.mtu = 1500

    d1_ip = d1_eth.ipv4_addresses.add(name="d1_ip")
    d1_ip.set(address=tc["p1Ip"], gateway=tc["p1Gateway"], prefix=tc["p1Prefix"])

    d1.bgp.router_id = tc["p1Ip"]

    d1_bgpv4 = d1.bgp.ipv4_interfaces.add(ipv4_name=d1_ip.name)

    d1_bgpv4_peer = d1_bgpv4.peers.add(name="d1_bgpv4_peer")
    d1_bgpv4_peer.set(
        as_number=tc["p1As"], as_type=d1_bgpv4_peer.EBGP, peer_address=tc["p1Gateway"]
    )
    d1_bgpv4_peer.learned_information_filter.set(
        unicast_ipv4_prefix=True, unicast_ipv6_prefix=True
    )

    d1_bgpv4_peer_rrv4 = d1_bgpv4_peer.v4_routes.add(name="d1_bgpv4_peer_rrv4")
    d1_bgpv4_peer_rrv4.set(
        next_hop_ipv4_address=tc["p1NextHopV4"],
        next_hop_address_type=d1_bgpv4_peer_rrv4.IPV4,
        next_hop_mode=d1_bgpv4_peer_rrv4.MANUAL,
    )

    d1_bgpv4_peer_rrv4.addresses.add(
        address=tc["p1AdvRouteV4"], prefix=32, count=tc["p1RouteCount"], step=1
    )

    d1_bgpv4_peer_rrv4.advanced.set(
        multi_exit_discriminator=50, origin=d1_bgpv4_peer_rrv4.advanced.EGP
    )

    d1_bgpv4_peer_rrv4_com = d1_bgpv4_peer_rrv4.communities.add(
        as_number=1,
        as_custom=2,
    )
    d1_bgpv4_peer_rrv4_com.type = d1_bgpv4_peer_rrv4_com.MANUAL_AS_NUMBER

    d1_bgpv4_peer_rrv4.as_path.as_set_mode = d1_bgpv4_peer_rrv4.as_path.INCLUDE_AS_SET

    d1_bgpv4_peer_rrv4_seg = d1_bgpv4_peer_rrv4.as_path.segments.add()
    d1_bgpv4_peer_rrv4_seg.set(
        as_numbers=[1112, 1113], type=d1_bgpv4_peer_rrv4_seg.AS_SEQ
    )

    d1_bgpv4_peer_rrv6 = d1_bgpv4_peer.v6_routes.add(name="d1_bgpv4_peer_rrv6")
    d1_bgpv4_peer_rrv6.set(
        next_hop_ipv6_address=tc["p1NextHopV6"],
        next_hop_address_type=d1_bgpv4_peer_rrv6.IPV6,
        next_hop_mode=d1_bgpv4_peer_rrv6.MANUAL,
    )

    d1_bgpv4_peer_rrv6.addresses.add(
        address=tc["p1AdvRouteV6"], prefix=128, count=tc["p1RouteCount"], step=1
    )

    d1_bgpv4_peer_rrv6.advanced.set(
        multi_exit_discriminator=50, origin=d1_bgpv4_peer_rrv6.advanced.EGP
    )

    d1_bgpv4_peer_rrv6_com = d1_bgpv4_peer_rrv6.communities.add(
        as_number=1, as_custom=2
    )
    d1_bgpv4_peer_rrv6_com.type = d1_bgpv4_peer_rrv6_com.MANUAL_AS_NUMBER

    d1_bgpv4_peer_rrv6.as_path.as_set_mode = d1_bgpv4_peer_rrv6.as_path.INCLUDE_AS_SET

    d1_bgpv4_peer_rrv6_seg = d1_bgpv4_peer_rrv6.as_path.segments.add()
    d1_bgpv4_peer_rrv6_seg.set(
        as_numbers=[1112, 1113], type=d1_bgpv4_peer_rrv6_seg.AS_SEQ
    )

    d2_eth = d2.ethernets.add(name="d2_eth")
    d2_eth.connection.port_name = p2.name
    d2_eth.mac = tc["p2Mac"]
    d2_eth.mtu = 1500

    d2_ip = d2_eth.ipv4_addresses.add(name="d2_ip")
    d2_ip.set(address=tc["p2Ip"], gateway=tc["p2Gateway"], prefix=tc["p2Prefix"])

    d2.bgp.router_id = tc["p2Ip"]

    d2_bgpv4 = d2.bgp.ipv4_interfaces.add()
    d2_bgpv4.ipv4_name = d2_ip.name

    d2_bgpv4_peer = d2_bgpv4.peers.add(name="d2_bgpv4_peer")
    d2_bgpv4_peer.set(
        as_number=tc["p2As"], as_type=d2_bgpv4_peer.EBGP, peer_address=tc["p2Gateway"]
    )
    d2_bgpv4_peer.learned_information_filter.set(
        unicast_ipv4_prefix=True, unicast_ipv6_prefix=True
    )

    d2_bgpv4_peer_rrv4 = d2_bgpv4_peer.v4_routes.add(name="d2_bgpv4_peer_rrv4")
    d2_bgpv4_peer_rrv4.set(
        next_hop_ipv4_address=tc["p2NextHopV4"],
        next_hop_address_type=d2_bgpv4_peer_rrv4.IPV4,
        next_hop_mode=d2_bgpv4_peer_rrv4.MANUAL,
    )

    d2_bgpv4_peer_rrv4.addresses.add(
        address=tc["p2AdvRouteV4"], prefix=32, count=tc["p2RouteCount"], step=1
    )

    d2_bgpv4_peer_rrv4.advanced.set(
        multi_exit_discriminator=50, origin=d2_bgpv4_peer_rrv4.advanced.EGP
    )

    d2_bgpv4_peer_rrv4_com = d2_bgpv4_peer_rrv4.communities.add(
        as_number=1, as_custom=2
    )
    d2_bgpv4_peer_rrv4_com.type = d2_bgpv4_peer_rrv4_com.MANUAL_AS_NUMBER

    d2_bgpv4_peer_rrv4.as_path.as_set_mode = d2_bgpv4_peer_rrv4.as_path.INCLUDE_AS_SET

    d2_bgpv4_peer_rrv4_seg = d2_bgpv4_peer_rrv4.as_path.segments.add()
    d2_bgpv4_peer_rrv4_seg.set(
        as_numbers=[1112, 1113], type=d2_bgpv4_peer_rrv4_seg.AS_SEQ
    )

    d2_bgpv4_peer_rrv6 = d2_bgpv4_peer.v6_routes.add(name="d2_bgpv4_peer_rrv6")
    d2_bgpv4_peer_rrv6.set(
        next_hop_ipv6_address=tc["p2NextHopV6"],
        next_hop_address_type=d2_bgpv4_peer_rrv6.IPV6,
        next_hop_mode=d2_bgpv4_peer_rrv6.MANUAL,
    )

    d2_bgpv4_peer_rrv6.addresses.add(
        address=tc["p2AdvRouteV6"], prefix=128, count=tc["p2RouteCount"], step=1
    )

    d2_bgpv4_peer_rrv6.advanced.set(
        multi_exit_discriminator=50, origin=d2_bgpv4_peer_rrv6.advanced.EGP
    )

    d2_bgpv4_peer_rrv6_com = d2_bgpv4_peer_rrv6.communities.add(
        as_number=1, as_custom=2
    )
    d2_bgpv4_peer_rrv6_com.type = d2_bgpv4_peer_rrv6_com.MANUAL_AS_NUMBER

    d2_bgpv4_peer_rrv6.as_path.as_set_mode = d2_bgpv4_peer_rrv6.as_path.INCLUDE_AS_SET

    d2_bgpv4_peer_rrv6_seg = d2_bgpv4_peer_rrv6.as_path.segments.add()
    d2_bgpv4_peer_rrv6_seg.set(
        as_numbers=[1112, 1113], type=d2_bgpv4_peer_rrv6_seg.AS_SEQ
    )

    for i in range(0, 4):
        f = c.flows.add()
        f.duration.fixed_packets.packets = tc["pktCount"]
        f.rate.pps = tc["pktRate"]
        f.size.fixed = tc["pktSize"]
        f.metrics.enable = True

    f1_v4 = c.flows[0]
    f1_v4.name = "f1_v4"
    f1_v4.tx_rx.device.set(
        tx_names=[d1_bgpv4_peer_rrv4.name], rx_names=[d2_bgpv4_peer_rrv4.name]
    )

    f1_v4_eth, f1_v4_ip, f1_v4_tcp = f1_v4.packet.ethernet().ipv4().tcp()
    f1_v4_eth.src.value = d1_eth.mac
    f1_v4_ip.src.value = tc["p1AdvRouteV4"]
    f1_v4_ip.dst.value = tc["p2AdvRouteV4"]
    f1_v4_tcp.src_port.value = 5000
    f1_v4_tcp.dst_port.value = 6000

    f1_v6 = c.flows[1]
    f1_v6.name = "f1_v6"
    f1_v6.tx_rx.device.set(
        tx_names=[d1_bgpv4_peer_rrv6.name], rx_names=[d2_bgpv4_peer_rrv6.name]
    )

    f1_v6_eth, f1_v6_ip, f1_v6_tcp = f1_v6.packet.ethernet().ipv6().tcp()
    f1_v6_eth.src.value = d1_eth.mac
    f1_v6_ip.src.value = tc["p1AdvRouteV6"]
    f1_v6_ip.dst.value = tc["p2AdvRouteV6"]
    f1_v6_tcp.src_port.value = 5000
    f1_v6_tcp.dst_port.value = 6000

    f2_v4 = c.flows[2]
    f2_v4.name = "f2_v4"
    f2_v4.tx_rx.device.set(
        tx_names=[d2_bgpv4_peer_rrv4.name], rx_names=[d1_bgpv4_peer_rrv4.name]
    )

    f2_v4_eth, f2_v4_ip, f2_v4_tcp = f2_v4.packet.ethernet().ipv4().tcp()
    f2_v4_eth.src.value = d2_eth.mac
    f2_v4_ip.src.value = tc["p2AdvRouteV4"]
    f2_v4_ip.dst.value = tc["p1AdvRouteV4"]
    f2_v4_tcp.src_port.value = 5000
    f2_v4_tcp.dst_port.value = 6000

    f2_v6 = c.flows[3]
    f2_v6.name = "f2_v6"
    f2_v6.tx_rx.device.set(
        tx_names=[d2_bgpv4_peer_rrv6.name], rx_names=[d1_bgpv4_peer_rrv6.name]
    )

    f2_v6_eth, f2_v6_ip, f2_v6_tcp = f2_v6.packet.ethernet().ipv6().tcp()
    f2_v6_eth.src.value = d2_eth.mac
    f2_v6_ip.src.value = tc["p2AdvRouteV6"]
    f2_v6_ip.dst.value = tc["p1AdvRouteV6"]
    f2_v6_tcp.src_port.value = 5000
    f2_v6_tcp.dst_port.value = 6000

    # print("Config:\n%s", c)
    return c

def bgp_metrics_ok(api, tc):
    for m in get_bgpv4_metrics(api):
        if (
            m.session_state == m.DOWN
            or m.routes_advertised != 2 * tc["p1RouteCount"]
            or m.routes_received != 2 * tc["p2RouteCount"]
        ):
            return False
    return True

def bgp_prefixes_ok(api, tc):
    prefix_count = 0
    for m in get_bgp_prefixes(api):
        for p in m.ipv4_unicast_prefixes:
            for key in ["p1", "p2"]:
                if (
                    p.ipv4_address == tc[key + "AdvRouteV4"]
                    and p.ipv4_next_hop == tc[key + "NextHopV4"]
                ):
                    prefix_count += 1
        for p in m.ipv6_unicast_prefixes:
            for key in ["p1", "p2"]:
                if (
                    p.ipv6_address == tc[key + "AdvRouteV6"]
                    and p.ipv6_next_hop == tc[key + "NextHopV6"]
                ):
                    prefix_count += 1

    return prefix_count == 4

def flow_metrics_ok(api, tc):
    for m in get_flow_metrics(api):
        if (
            m.transmit != m.STOPPED
            or m.frames_tx != tc["pktCount"]
            or m.frames_rx != tc["pktCount"]
        ):
            return False
    return True

def get_bgpv4_metrics(api):
    print("%s Getting bgpv4 metrics    ..." % datetime.now())
    req = api.metrics_request()
    req.bgpv4.peer_names = []

    metrics = api.get_metrics(req).bgpv4_metrics

    tb = Table(
        "BGPv4 Metrics",
        [
            "Name",
            "State",
            "Routes Adv.",
            "Routes Rec.",
        ],
    )

    for m in metrics:
        tb.append_row(
            [
                m.name,
                m.session_state,
                m.routes_advertised,
                m.routes_received,
            ]
        )

    print(tb)
    return metrics

def get_bgp_prefixes(api):
    print("%s Getting BGP prefixes    ..." % datetime.now())
    req = api.states_request()
    req.bgp_prefixes.bgp_peer_names = []
    bgp_prefixes = api.get_states(req).bgp_prefixes

    tb = Table(
        "BGP Prefixes",
        [
            "Name",
            "IPv4 Address",
            "IPv4 Next Hop",
            "IPv6 Address",
            "IPv6 Next Hop",
        ],
        20,
    )

    for b in bgp_prefixes:
        for p in b.ipv4_unicast_prefixes:
            tb.append_row(
                [
                    b.bgp_peer_name,
                    "{}/{}".format(p.ipv4_address, p.prefix_length),
                    p.ipv4_next_hop,
                    "",
                    "" if p.ipv6_next_hop is None else p.ipv6_next_hop,
                ]
            )
        for p in b.ipv6_unicast_prefixes:
            tb.append_row(
                [
                    b.bgp_peer_name,
                    "",
                    "" if p.ipv4_next_hop is None else p.ipv4_next_hop,
                    "{}/{}".format(p.ipv6_address, p.prefix_length),
                    p.ipv6_next_hop,
                ]
            )

    print(tb)
    return bgp_prefixes

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
    Test_ebgp_route_prefix()
