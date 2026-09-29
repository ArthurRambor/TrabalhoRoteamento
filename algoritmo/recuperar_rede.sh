#!/bin/bash

# Recupera os enderecos IP e rotas da topologia de roteamento.
# Executar depois que os containers e links estiverem ativos.

set -e

echo "Iniciando recuperacao da rede..."

# Roteador R1
docker exec clab-roteamento-r1 sh -c '
ip link set eth1 up
ip addr replace 10.0.12.1/30 dev eth1
ip link set eth2 up
ip addr replace 10.0.15.2/30 dev eth2
ip link set eth3 up
ip addr replace 10.0.13.1/30 dev eth3
ip link set eth4 up
ip addr replace 192.168.10.1/24 dev eth4
'

# Roteador R2
docker exec clab-roteamento-r2 sh -c '
ip link set eth1 up
ip addr replace 10.0.12.2/30 dev eth1
ip link set eth2 up
ip addr replace 10.0.23.1/30 dev eth2
'

# Roteador R3
docker exec clab-roteamento-r3 sh -c '
ip link set eth1 up
ip addr replace 10.0.23.2/30 dev eth1
ip link set eth2 up
ip addr replace 10.0.34.1/30 dev eth2
ip link set eth3 up
ip addr replace 10.0.13.2/30 dev eth3
ip link set eth4 up
ip addr replace 10.0.35.1/30 dev eth4
'

# Roteador R4
docker exec clab-roteamento-r4 sh -c '
ip link set eth1 up
ip addr replace 10.0.34.2/30 dev eth1
ip link set eth2 up
ip addr replace 10.0.45.1/30 dev eth2
'

# Roteador R5
docker exec clab-roteamento-r5 sh -c '
ip link set eth1 up
ip addr replace 10.0.45.2/30 dev eth1
ip link set eth2 up
ip addr replace 10.0.15.1/30 dev eth2
ip link set eth3 up
ip addr replace 10.0.35.2/30 dev eth3
ip link set eth4 up
ip addr replace 192.168.50.1/24 dev eth4
'

# Host A
docker exec clab-roteamento-host-a sh -c '
ip link set eth1 up
ip addr replace 192.168.10.10/24 dev eth1
ip route replace default via 192.168.10.1
'

# Host B
docker exec clab-roteamento-host-b sh -c '
ip link set eth1 up
ip addr replace 192.168.50.10/24 dev eth1
ip route replace default via 192.168.50.1
'

echo "Recuperacao dos enderecos e rotas concluida."
