#!/bin/bash
docker run -it --name client1 --network client_net -v client1_data:/app client_image
docker run -it --name client2 --network client_net -v client2_data:/app client_image