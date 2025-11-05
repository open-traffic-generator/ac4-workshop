# Lab 03 Instructions

## Overview

This lab uses [**containerlab**](https://containerlab.dev/) to deploy a clos topology (3 leafs and 2 spines) using [**Arista ceos**](https://containerlab.dev/manual/kinds/ceos/) and one Ixia-c-one container with 3 interfaces connected to the 3 leaf nodes. The routers are preconfigured with evpn and the Ixia-c ports are in their own L2 domain.

The included test script has 6 flows, one for each port to port direction, and the goal of the lab is to run traffic between the leaf nodes and observe the effects when network operations are executed.

Deployment and logical topology below

![alt text](../Docs/images/lab-03/lab3-1.png)

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


