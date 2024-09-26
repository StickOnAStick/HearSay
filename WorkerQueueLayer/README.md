# Worker Queue Layer

Reference the DrawIo schematic found in `DesignDocuments/v0.0.0.drawio`.

This directory hosts the RabbitMQ message (work) broker as well as the code for each worker. 

Workers have a top level utils package they import to perform aggregation. All workers have connections to DB and cache. 

We use a Docker image of RabbitMQ for production ease and scale. Read more about using this [here](https://hub.docker.com/_/rabbitmq/). 

# Setup and spin-up

First make sure you have docker installed on your machine. You can do so [here](https://docs.docker.com/engine/install/ubuntu/).

## IMPORTANT DOCKER INFO
By default, __all external source IPs are allowed to connect to ports that have been published to the Docker host's addresses.__

To allow only a specific IP or network to access the containers, insert a negated rule at the top of the DOCKER-USER filter chain. For example, the following rule drops packets from all IP addresses except __192.0.2.2__:

 `iptables -I DOCKER-USER -i ext_if ! -s 192.0.2.2 -j DROP`

## SpinUp

Navigate to the RabbitMQ server and run:
`sudo docker run -d --memory={your_ammount}(b,k,m,g) --hostname hearysay_rabbit --name rabbit1 rabbitmq:3`

You can check that the containers running by entering `sudo docker ps` where you should find:
`someID   rabbitmq:3   "docker-entrypoint.s…" ... 4369/tcp, 5671-5672/tcp, 15691-15692/tcp, 25672/tcp   rabbit1`

RabbitMQ uses __Port 5672__ by default. You will need to allow this port in your UFW / IP tables for docker.


## Shutdown

To stop the docker container use `sudo docker stop rabbit1`