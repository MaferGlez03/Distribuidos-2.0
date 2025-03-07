#!/bin/bash
docker run -dit --name server1 --network chord_net -p 8000:8000 -v server1_data:/app chord_server_image
docker run -dit --name server2 --network chord_net -p 8001:8000 -v server2_data:/app chord_server_image
docker run -dit --name server3 --network chord_net -p 8002:8000 -v server3_data:/app chord_server_image
