# Lab 04 Instructions

## Overview

In this lab we will use [**kne**](https://github.com/openconfig/kne) (Kubernetes Network Emulation) and [**kind**](https://kind.sigs.k8s.io/) (Kubernetes In Docker) to deploy a two otg ports plus one device under test topology. Similarily to containerlab, kne uses configuration files to deploy test topologies over k8s clusters. [**Ixia-c**](https://ixia-c.dev) uses the [**keng operator**](https://github.com/open-traffic-generator/keng-operator) component which assists in the otg ports deployment.
We will use both **snappi** and **gosnappi** to run the provided script and we will also run an openconfig [**featureprofiles**](https://github.com/openconfig/featureprofiles) test.

Deployment and logical topology below


## Prerequisites

- If **containerlab** is not installed please do so.

```Shell
bash -c "$(curl -sL https://get.containerlab.dev)"
```

- snappi must be installed at this point. If not, use the command below to do it.

```Shell
python3 -m pip install --upgrade snappi --break-system-packages
```


## Execution



