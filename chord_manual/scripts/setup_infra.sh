#!/bin/bash
docker network create --subnet=172.25.0.0/24 chord_net
docker network create --subnet=172.25.1.0/24 client_net