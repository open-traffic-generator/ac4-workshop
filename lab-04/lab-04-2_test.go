package main

import (
	"fmt"
	"net"
	"slices"
	"testing"
	"time"

	"github.com/open-traffic-generator/conformance/helpers/table"
	"github.com/open-traffic-generator/snappi/gosnappi"
)

func TestEbgpRoutePrefix(t *testing.T) {

	testConst := map[string]interface{}{
		// "controller_location": "filled by user for http transport",
		"controller_location": "filled by user for grpc transport",
		"p1_location":         "filled by user",
		"p2_location":         "filled by user",
		"pktRate":             uint64(200),
		"pktCount":            uint32(12000),
		"pktSize":             uint32(128),
		"p1Mac":               "00:00:01:01:01:01",
		"p1Ip":                "192.168.11.2",
		"p1Gateway":           "192.168.11.1",
		"p1Prefix":            uint32(24),
		"p1As":                uint32(1111),
		"p2Mac":               "00:00:01:01:01:02",
		"p2Ip":                "192.168.22.2",
		"p2Gateway":           "192.168.22.1",
		"p2Prefix":            uint32(24),
		"p2As":                uint32(1112),
		"routeCount":          uint32(3),
		"p1AdvRouteV4":        "101.1.1.1",
		"p2AdvRouteV4":        "201.2.2.1",
	}

	api := gosnappi.NewApi()

	// api.NewHttpTransport().SetLocation(testConst["controller_location"].(string))
	api.NewGrpcTransport().SetLocation(testConst["controller_location"].(string))

	c := ebgpRoutePrefixConfig(testConst)

	api.SetConfig(c)

	startProtocols(t, api)

	/* Check if BGP sessions are up and expected routes are Txed and Rxed */
	waitFor(t,
		func() bool { return bgpMetricsOk(t, api, testConst) },
		waitForOpts{FnName: "waiting for bgp neighbours", Interval: 2 * time.Second, Timeout: 30 * time.Second},
	)

	/* Check if each BGP session recieved routes with expected attributes */
	waitFor(t,
		func() bool { return bgpPrefixesOk(t, api, testConst) },
		waitForOpts{FnName: "wait for bgp route prefixes", Interval: 2 * time.Second, Timeout: 30 * time.Second},
	)

	startTransmit(t, api)

	waitFor(t,
		func() bool { return flowMetricsOk(t, api, testConst) },
		waitForOpts{FnName: "wait for flow metrics", Interval: 2 * time.Second, Timeout: 90 * time.Second},
	)
}

type waitForOpts struct {
	FnName   string
	Interval time.Duration
	Timeout  time.Duration
}

func ebgpRoutePrefixConfig(tc map[string]interface{}) gosnappi.Config {

	c := gosnappi.NewConfig()

	p1 := c.Ports().Add().SetName("p1").SetLocation(tc["p1_location"].(string))
	p2 := c.Ports().Add().SetName("p2").SetLocation(tc["p2_location"].(string))

	dp1 := c.Devices().Add().SetName("dp1")
	dp2 := c.Devices().Add().SetName("dp2")

	dp1Eth := dp1.Ethernets().
		Add().
		SetName("dp1Eth").
		SetMac(tc["p1Mac"].(string)).
		SetMtu(1500)

	dp1Eth.Connection().SetPortName(p1.Name())

	dp1Ip := dp1Eth.
		Ipv4Addresses().
		Add().
		SetName("dp1Ip").
		SetAddress(tc["p1Ip"].(string)).
		SetGateway(tc["p1Gateway"].(string)).
		SetPrefix(tc["p1Prefix"].(uint32))

	dp1Bgp := dp1.Bgp().
		SetRouterId(tc["p1Ip"].(string))

	dp1Bgpv4 := dp1Bgp.
		Ipv4Interfaces().Add().
		SetIpv4Name(dp1Ip.Name())

	dp1Bgpv4Peer := dp1Bgpv4.
		Peers().
		Add().
		SetAsNumber(tc["p1As"].(uint32)).
		SetAsType(gosnappi.BgpV4PeerAsType.EBGP).
		SetPeerAddress(tc["p1Gateway"].(string)).
		SetName("dp1Bgpv4Peer")

	dp1Bgpv4Peer.LearnedInformationFilter().SetUnicastIpv4Prefix(true).SetUnicastIpv6Prefix(true)

	dp1Bgpv4PeerRrV4 := dp1Bgpv4Peer.V4Routes().Add().SetName("dp1Bgpv4PeerRrV4")

	dp1Bgpv4PeerRrV4.Addresses().Add().
		SetAddress(tc["p1AdvRouteV4"].(string)).
		SetPrefix(32).
		SetCount(tc["routeCount"].(uint32)).
		SetStep(1)

	dp1Bgpv4PeerRrV4.Advanced().
		SetMultiExitDiscriminator(50).
		SetOrigin(gosnappi.BgpRouteAdvancedOrigin.EGP)

	dp1Bgpv4PeerRrV4.Communities().Add().
		SetAsNumber(1).
		SetAsCustom(2).
		SetType(gosnappi.BgpCommunityType.MANUAL_AS_NUMBER)

	dp1Bgpv4PeerRrV4AsPath := dp1Bgpv4PeerRrV4.AsPath().
		SetAsSetMode(gosnappi.BgpAsPathAsSetMode.INCLUDE_AS_SET)

	dp1Bgpv4PeerRrV4AsPath.Segments().Add().
		SetAsNumbers([]uint32{1112, 1113}).
		SetType(gosnappi.BgpAsPathSegmentType.AS_SEQ)

	dp2Eth := dp2.Ethernets().
		Add().
		SetName("dp2Eth").
		SetMac(tc["p2Mac"].(string)).
		SetMtu(1500)

	dp2Eth.Connection().SetPortName(p2.Name())

	dp2Ip := dp2Eth.
		Ipv4Addresses().
		Add().
		SetName("dp2Ip").
		SetAddress(tc["p2Ip"].(string)).
		SetGateway(tc["p2Gateway"].(string)).
		SetPrefix(tc["p2Prefix"].(uint32))

	dp2Bgp := dp2.Bgp().
		SetRouterId(tc["p2Ip"].(string))

	dp2Bgpv4 := dp2Bgp.
		Ipv4Interfaces().Add().
		SetIpv4Name(dp2Ip.Name())

	dp2Bgpv4Peer := dp2Bgpv4.
		Peers().
		Add().
		SetAsNumber(tc["p2As"].(uint32)).
		SetAsType(gosnappi.BgpV4PeerAsType.EBGP).
		SetPeerAddress(tc["p2Gateway"].(string)).
		SetName("dp2Bgpv4Peer")

	dp2Bgpv4Peer.LearnedInformationFilter().SetUnicastIpv4Prefix(true).SetUnicastIpv6Prefix(false)

	dp2Bgpv4PeerRrV4 := dp2Bgpv4Peer.V4Routes().Add().SetName("dp2Bgpv4PeerRrV4")

	dp2Bgpv4PeerRrV4.Addresses().Add().
		SetAddress(tc["p2AdvRouteV4"].(string)).
		SetPrefix(32).
		SetCount(tc["routeCount"].(uint32)).
		SetStep(1)

	dp2Bgpv4PeerRrV4.Advanced().
		SetMultiExitDiscriminator(50).
		SetOrigin(gosnappi.BgpRouteAdvancedOrigin.EGP)

	dp2Bgpv4PeerRrV4.Communities().Add().
		SetAsNumber(1).
		SetAsCustom(2).
		SetType(gosnappi.BgpCommunityType.MANUAL_AS_NUMBER)

	dp2Bgpv4PeerRrV4AsPath := dp2Bgpv4PeerRrV4.AsPath().
		SetAsSetMode(gosnappi.BgpAsPathAsSetMode.INCLUDE_AS_SET)

	dp2Bgpv4PeerRrV4AsPath.Segments().Add().
		SetAsNumbers([]uint32{4444}).
		SetType(gosnappi.BgpAsPathSegmentType.AS_SEQ)

	for i := 1; i <= 2; i++ {
		flow := c.Flows().Add()
		flow.Duration().FixedPackets().SetPackets(tc["pktCount"].(uint32))
		flow.Rate().SetPps(tc["pktRate"].(uint64))
		flow.Size().SetFixed(tc["pktSize"].(uint32))
		flow.Metrics().SetEnable(true)
	}

	fp1V4 := c.Flows().Items()[0]
	fp1V4.SetName("fp1V4")
	fp1V4.TxRx().Device().
		SetTxNames([]string{dp1Bgpv4PeerRrV4.Name()}).
		SetRxNames([]string{dp2Bgpv4PeerRrV4.Name()})

	fp1V4Eth := fp1V4.Packet().Add().Ethernet()
	fp1V4Eth.Src().SetValue(dp1Eth.Mac())

	fp1V4Ip := fp1V4.Packet().Add().Ipv4()
	fp1V4Ip.Src().SetValue(tc["p1AdvRouteV4"].(string))
	fp1V4Ip.Dst().SetValue(tc["p2AdvRouteV4"].(string))

	fp1V4Udp := fp1V4.Packet().Add().Udp()
	fp1V4Udp.SrcPort().SetValue(5000)
	fp1V4Udp.DstPort().SetValue(6000)

	fp2V4 := c.Flows().Items()[1]
	fp2V4.SetName("fp2V4")
	fp2V4.TxRx().Device().
		SetTxNames([]string{dp2Bgpv4PeerRrV4.Name()}).
		SetRxNames([]string{dp1Bgpv4PeerRrV4.Name()})

	fp2V4Eth := fp2V4.Packet().Add().Ethernet()
	fp2V4Eth.Src().SetValue(dp2Eth.Mac())

	fp2V4Ip := fp2V4.Packet().Add().Ipv4()
	fp2V4Ip.Src().SetValue(tc["p2AdvRouteV4"].(string))
	fp2V4Ip.Dst().SetValue(tc["p1AdvRouteV4"].(string))

	fp2V4Udp := fp2V4.Packet().Add().Udp()
	fp2V4Udp.SrcPort().SetValue(6000)
	fp2V4Udp.DstPort().SetValue(5000)

	return c
}

func bgpMetricsOk(t *testing.T, api gosnappi.Api, tc map[string]interface{}) bool {
	for _, m := range getBgpv4Metrics(t, api) {
		if m.SessionState() == gosnappi.Bgpv4MetricSessionState.DOWN ||
			m.RoutesAdvertised() != uint64(tc["routeCount"].(uint32)) ||
			m.RoutesReceived() != uint64(tc["routeCount"].(uint32)) {
			return false
		}
	}
	return true
}

func bgpPrefixesOk(t *testing.T, api gosnappi.Api, tc map[string]interface{}) bool {

	var p1ExpectedRoutesV4 []string
	var p2ExpectedRoutesV4 []string

	for i := 0; i <= int(tc["routeCount"].(uint32)); i++ {
		p1ExpectedRoutesV4 = append(p1ExpectedRoutesV4, incrementIPv4(net.ParseIP(tc["p2AdvRouteV4"].(string)), uint32(i)).String())
		p2ExpectedRoutesV4 = append(p2ExpectedRoutesV4, incrementIPv4(net.ParseIP(tc["p1AdvRouteV4"].(string)), uint32(i)).String())
	}

	prefixCount := 0
	for _, m := range getBgpPrefixes(t, api) {
		for _, p := range m.Ipv4UnicastPrefixes().Items() {
			if m.BgpPeerName() == "dp1Bgpv4Peer" {
				if slices.Contains(p1ExpectedRoutesV4, p.Ipv4Address()) && p.Ipv4NextHop() == tc["p1Gateway"].(string) {
					prefixCount += 1
				}
			}
			if m.BgpPeerName() == "dp2Bgpv4Peer" {
				if slices.Contains(p2ExpectedRoutesV4, p.Ipv4Address()) && p.Ipv4NextHop() == tc["p2Gateway"].(string) {
					prefixCount += 1
				}
			}
		}
	}
	fmt.Printf("DEBUG: prefixCount=%d\n", prefixCount)
	return prefixCount == 2*int(tc["routeCount"].(uint32))
}

func flowMetricsOk(t *testing.T, api gosnappi.Api, tc map[string]interface{}) bool {
	pktCount := uint64(tc["pktCount"].(uint32))

	for _, m := range getFlowMetrics(t, api) {
		if m.Transmit() != gosnappi.FlowMetricTransmit.STOPPED ||
			m.FramesTx() != pktCount ||
			m.FramesRx() != pktCount {
			return false
		}

	}

	return true
}

func startProtocols(t *testing.T, api gosnappi.Api) {
	cs := gosnappi.NewControlState()
	cs.Protocol().All().SetState(gosnappi.StateProtocolAllState.START)

	if _, err := api.SetControlState(cs); err != nil {
		t.Fatal(err)
	}
}

func startTransmit(t *testing.T, api gosnappi.Api) {
	cs := gosnappi.NewControlState()
	cs.Traffic().FlowTransmit().SetState(gosnappi.StateTrafficFlowTransmitState.START)

	if _, err := api.SetControlState(cs); err != nil {
		t.Fatal(err)
	}
}

func getFlowMetrics(t *testing.T, api gosnappi.Api) []gosnappi.FlowMetric {

	t.Log("Getting flow metrics ...")

	mr := gosnappi.NewMetricsRequest()
	mr.Flow()
	res, _ := api.GetMetrics(mr)

	tb := table.NewTable(
		"Flow Metrics",
		[]string{
			"Name",
			"State",
			"Frames Tx",
			"Frames Rx",
			"FPS Tx",
			"FPS Rx",
			"bps Tx",
			"bps Rx",
			"Bytes Tx",
			"Bytes Rx",
		},
		15,
	)
	for _, v := range res.FlowMetrics().Items() {
		if v != nil {
			tb.AppendRow([]interface{}{
				v.Name(),
				v.Transmit(),
				v.FramesTx(),
				v.FramesRx(),
				v.FramesTxRate(),
				v.FramesRxRate(),
				v.TxRateBps(),
				v.RxRateBps(),
				v.BytesTx(),
				v.BytesRx(),
			})
		}
	}

	t.Log(tb.String())
	return res.FlowMetrics().Items()
}

func getBgpv4Metrics(t *testing.T, api gosnappi.Api) []gosnappi.Bgpv4Metric {
	t.Log("Getting bgpv4 metrics ...")

	mr := gosnappi.NewMetricsRequest()
	mr.Bgpv4()
	res, _ := api.GetMetrics(mr)

	tb := table.NewTable(
		"BGPv4 Metrics",
		[]string{
			"Name",
			"State",
			"Routes Adv.",
			"Routes Rec.",
		},
		15,
	)
	for _, v := range res.Bgpv4Metrics().Items() {
		if v != nil {
			tb.AppendRow([]interface{}{
				v.Name(),
				v.SessionState(),
				v.RoutesAdvertised(),
				v.RoutesReceived(),
			})
		}
	}

	t.Log(tb.String())
	return res.Bgpv4Metrics().Items()
}

func getBgpPrefixes(t *testing.T, api gosnappi.Api) []gosnappi.BgpPrefixesState {

	t.Log("Getting BGP Prefixes ...")

	sr := gosnappi.NewStatesRequest()
	sr.BgpPrefixes()
	res, _ := api.GetStates(sr)
	// log.Println(res)

	tb := table.NewTable(
		"BGP Prefixes",
		[]string{
			"Name",
			"IPv4 Address",
			"IPv4 Next Hop",
		},
		20,
	)

	for _, v := range res.BgpPrefixes().Items() {

		for _, w := range v.Ipv4UnicastPrefixes().Items() {
			row := []interface{}{
				v.BgpPeerName(), fmt.Sprintf("%s/%d", w.Ipv4Address(), w.PrefixLength()), w.Ipv4NextHop(), "",
			}

			tb.AppendRow(row)
		}
	}

	t.Log(tb.String())
	return res.BgpPrefixes().Items()
}

func incrementIPv4(ip net.IP, amount uint32) net.IP {

	ipInt := ipToUint32(ip)
	ipInt += amount

	return uint32ToIP(ipInt)
}

func ipToUint32(ip net.IP) uint32 {
	ip = ip.To4()
	return uint32(ip[0])<<24 | uint32(ip[1])<<16 | uint32(ip[2])<<8 | uint32(ip[3])
}

// uint32ToIP converts a uint32 to a net.IP (IPv4).
func uint32ToIP(ipInt uint32) net.IP {
	ip := make(net.IP, 4)
	ip[0] = byte((ipInt >> 24) & 0xFF)
	ip[1] = byte((ipInt >> 16) & 0xFF)
	ip[2] = byte((ipInt >> 8) & 0xFF)
	ip[3] = byte(ipInt & 0xFF)
	return ip
}

func waitFor(t *testing.T, fn func() bool, opts waitForOpts) {

	if opts.Interval == 0 {
		opts.Interval = 500 * time.Millisecond
	}
	if opts.Timeout == 0 {
		opts.Timeout = 10 * time.Second
	}

	start := time.Now()
	t.Logf("Waiting for %s ...\n", opts.FnName)

	for {

		if fn() {
			t.Logf("Done waiting for %s\n", opts.FnName)
			return
		}

		if time.Since(start) > opts.Timeout {
			t.Fatalf("ERROR: Timeout occurred while waiting for %s\n", opts.FnName)
		}
		time.Sleep(opts.Interval)
	}
}
