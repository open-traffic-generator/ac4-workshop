# Lab 04 Instructions

## Overview

In this lab we will use [**kne**](https://github.com/openconfig/kne) (Kubernetes Network Emulation) and [**kind**](https://kind.sigs.k8s.io/) (Kubernetes In Docker) to deploy a two otg ports plus one device under test topology. Similarily to containerlab, kne uses configuration files to deploy test topologies over k8s clusters. [**Ixia-c**](https://ixia-c.dev) uses the [**keng operator**](https://github.com/open-traffic-generator/keng-operator) component which assists in the otg ports deployment.
We will use both **snappi** and **gosnappi** to run the provided script and we will also run an openconfig [**featureprofiles**](https://github.com/openconfig/featureprofiles) test.

The goal of this lab is to familiarize the users with gosnappi and kne concepts but also with running tests over kubernetes clusters

Deployment and logical topology below

![alt text](../Docs/images/lab-04/lab4-1.png)

## Prerequisites

- snappi must be installed at this point. If not, use the command below to do it.

```Shell
python3 -m pip install --upgrade snappi --break-system-packages
```

- Install **kind**. This will allow us to create a single node kubernetes cluster.

```Shell
[ $(uname -m) = x86_64 ] && curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.30.0/kind-linux-amd64
cd && chmod +x ./kind
sudo mv ./kind /usr/local/bin/kind
```

- Install **kubectl**. This utility allow us to control the k8s cluster.

```Shell
cd && curl -LO https://dl.k8s.io/release/v1.34.0/bin/linux/amd64/kubectl
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
```

- Install **kne**. 

```Shell
cd
wget https://github.com/openconfig/kne/archive/refs/tags/v0.3.0.tar.gz && tar -xvzf v0.3.0.tar.gz
cd kne-0.3.0 && make install
```

- Clone **featureprofiles** repository. These tests define groups of [***OpenConfig***](https://github.com/openconfig/public) paths that can be invoked on network devices.

```Shell
cd && git clone https://github.com/openconfig/featureprofiles.git
```

## Execution

- Create the kind cluster

```Shell
cd ~/ac4-workshop/lab-04/ && kne deploy kind-bridge.yaml
```

- Load images into the k8s cluster by running the **load-images.sh** utility.

```Shell
./load-images.sh
```

- Deploy the kne topology

```Shell
kne create ixia-c-ceos.textproto
```

## Cleanup

```Shell
kind delete cluster --name kne
```
