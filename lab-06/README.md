# Lab 06 Instructions

## Overview
In this lab we're going to use [**Cyperf**](https://www.keysight.com/us/en/products/network-test/cloud-test/cyperf.html) to generate http traffic between 2 cloud VMs (Cyperf Agents).
The goal of the lab is to get familiar with Cyperf architecture and how to deploy Cyperf agents using docker containers. We will also create simple tests to generate mixed traffic between the 2 agents and monitor the traffic using the Cyperf controller UI.


## Prerequisites

We will assign **VM1** as Cyperf Client Agent and **VM2** as Cyperf Server Agent.

## Client Configuration

- On VM1 creat the client docker network. Create a network with the subnet 172.21.X.0/24 where **X** is your assigned student number.

```Shell
docker network create --subnet=172.21.x.0/24 cyperf_mgmt_net
```

- Use your name to label the container properly. For example, if your name is John, use: ***--name john-client***
- Each student should replace ***CONTROLLER_ADDRESS*** with the IP address of the controller VM provided in your lab environment.
- Assign Client IP Address. Choose an IP address within the **172.21.X.0/24** subnet, ensuring it’s different from the server’s IP. Example: **172.21.6.4**

- Deploy the Client Agent. The CyPerf agent image may take a little while to download. Deploy the client using the command below.

```Shell
docker run -td --cap-add=NET_ADMIN --cap-add=IPC_LOCK \
--network cyperf_mgmt_net --ip=172.21.6.4 \
--name john-client                        \
-e AGENT_CONTROLLER=CONTROLLER_ADDRESS    \
-e AGENT_TAGS=john-client                 \
public.ecr.aws/keysight/cyperf-agent:latest
```

## Server Configuration

- On VM2 creat the server docker network. Create a network with the subnet 172.21.X.0/24 where **X** is your assigned student number.

```Shell
docker network create --subnet=172.21.x.0/24 cyperf_mgmt_net
```

- Use your name to label the container properly. For example, if your name is John, use: ***--name john-server***
- Each student should replace ***CONTROLLER_ADDRESS*** with the IP address of the controller VM provided in your lab environment.

- Assign Server IP Address. Choose an IP address within the **172.21.X.0/24** subnet, ensuring it’s different from the client's IP. Example: **172.21.6.5**

- In the server case you need to specify the port example **-p 80:80**. This ensures the docker agent is listening to the port 80 for any incoming request from the client agent.

- Deploy the Server Agent. The CyPerf agent image may take a little while to download. Deploy the server using the command below.

```Shell
sudo docker run -td --cap-add=NET_ADMIN --cap-add=IPC_LOCK \
--network cyperf_mgmt_net --ip=172.21.6.5                  \
--name john-server                                         \
-e AGENT_CONTROLLER=CONTROLLER_ADDRESS                     \
-e AGENT_TAGS=john-server                                  \
-p 80:80                                                   \
public.ecr.aws/keysight/cyperf-agent:latest
```
- Note your VM’s interface IP, retrievable via `ip addr` or `ifconfig`. This will serve as your Device Under Test(DUT) IP in the test as the docker client agent that we deployed earlier will send the traffic to this IP. This will internally get routed to the docker server we just deployed.
In this case, we will be using **ens6** IP address.

![alt text](../Docs/images/lab-06/lab6-1.png)

## Running the Test

- Access the Cyperf controller UI by navigating to `http://CONTROLLER_ADDRESS` in your web browser. Each student should replace ***CONTROLLER_ADDRESS*** with the IP address of the controller VM provided in your lab environment.

- Log in using the default credentials: Username: `your email address` Password: `Ixia123!`

- After logging in, you’ll see a preconfigured “lab-06-test” test session. The objective of this test is to generate 100 connections per second using simple HTTP traffic. Click to open it. 

![alt text](../Docs/images/lab-06/lab6-2.png)

- Then we go to the "ENTERPRISEMIX" section.

![alt text](../Docs/images/lab-06/lab6-3.png)

- In the test view, locate the exclamation marks beside the agent slots. Click on them to add agents.
- On the left-hand side, assign the client's port icon.
- You need to find and assign agents. A search by IP Address will ensure that we won't use someone else's agents. In my case `172.21.6`.

![alt text](../Docs/images/lab-06/lab6-10.png)

- You should find 2 addresses `172.21.X.4` and `172.21.X.5`, where **X** is your assigned student number. In my example I used 172.21.6.4 while deploying the client docker agent. In your case it should be `172.21.X.4`. Select that and click Update.

![alt text](../Docs/images/lab-06/lab6-4.png)

- On the right-hand side, assign the server IP. Should be `172.21.X.5` and click Update

![alt text](../Docs/images/lab-06/lab6-5.png)

- Open the DUT Configuration Panel by clicking on the DUT tab or section.

![alt text](../Docs/images/lab-06/lab6-6.png)

- Set the DUT IP Address. Enter the VM’s interface IP captured earlier on VM2.

![alt text](../Docs/images/lab-06/lab6-7.png)

- Start the Test. Click **START TEST** (blue play icon) to initiate the test.

![alt text](../Docs/images/lab-06/lab6-8.png)

- Once the test begins, navigate to the Statistics tab. Monitor live test metrics such as throughput, latency, connection count, and success/failure ratios

![alt text](../Docs/images/lab-06/lab6-9.png)


- We can now make some changes to the test objective for testing throughput and to include more applications to our mix of traffic. Click on top-right **Overview** to go back to the test configuration page, then edit the **Objectives & Timeline** section.

![alt text](../Docs/images/lab-06/lab6-12.png)

- Set the **Primary Objective** to **Throughput** and set the value to **100 Mbps** with a duration of **60** seconds. 

![alt text](../Docs/images/lab-06/lab6-13.png)


- Then click on **Applications** to add activate all applications of the mix.

![alt text](../Docs/images/lab-06/lab6-14.png)

- Restart the test by clicking on **START TEST** (blue play icon) to initiate the test and observe the new metrics.

![alt text](../Docs/images/lab-06/lab6-15.png)

- We can now enable the **ATTACK PROFILE** to simulate some DDoS traffic. Go back to the **Overview** page and then click on the **TEST SETTINGS** section. We're adding 2 attack profiles: **Critical Strikes** and **All Dan Gemini AI LLM Prompt Injection**. 

![alt text](../Docs/images/lab-06/lab6-16.png)

- More on the attack profiles can be found if you go and edit the **ATTACK PROFILE** section. There you can find a description for each strike. These attacks will be added to the existing traffic mix. 

![alt text](../Docs/images/lab-06/lab6-17.png)

- Restart the test by clicking on **START TEST** to initiate the test and observe the new metrics.

![alt text](../Docs/images/lab-06/lab6-18.png)


## Cleanup

On both VMs, run the commands below to remove the containers and the docker network.

```Shell
docker stop $(docker ps -aq) && docker rm $(docker ps -aq)
docker network rm cyperf_mgmt_net 
```
