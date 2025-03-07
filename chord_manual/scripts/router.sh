#!/bin/bash

# Activar el reenvío de paquetes
echo 1 > /proc/sys/net/ipv4/ip_forward

# Borrar reglas antiguas
iptables -F
iptables -t nat -F
iptables -t nat -X
iptables -X

# Permitir tráfico entre client_net y chord_net
iptables -A FORWARD -i eth0 -o eth1 -j ACCEPT
iptables -A FORWARD -i eth1 -o eth0 -j ACCEPT

# Habilitar NAT para reenviar tráfico correctamente
iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
iptables -t nat -A POSTROUTING -o eth1 -j MASQUERADE

# Permitir tráfico UDP en el puerto 8888 (DISCOVER)
iptables -A INPUT -p udp --dport 8888 -j ACCEPT
iptables -A FORWARD -p udp --dport 8888 -j ACCEPT

echo "Router configurado correctamente"

