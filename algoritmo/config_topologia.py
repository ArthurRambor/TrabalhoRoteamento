"""
Configuração do algoritmo de troca de rotas.
Laboratório isolado: roteamento-algoritmo.
"""

CONTAINERS = {
    "r1": "clab-roteamento-algoritmo-r1",
    "r2": "clab-roteamento-algoritmo-r2",
    "r3": "clab-roteamento-algoritmo-r3",
    "r4": "clab-roteamento-algoritmo-r4",
    "r5": "clab-roteamento-algoritmo-r5",
    "host-a": "clab-roteamento-algoritmo-host-a",
    "host-b": "clab-roteamento-algoritmo-host-b",
}

MONITOR_FROM = "r1"
MONITOR_TARGET_IP = "10.10.12.2"

REDE_ORIGEM = "192.168.110.0/24"
REDE_DESTINO = "192.168.150.0/24"

HOST_A_IP = "192.168.110.10"
HOST_B_IP = "192.168.150.10"

# (roteador, rede, próximo salto principal, próximo salto alternativo)
ROTAS = [
    ("r1", REDE_DESTINO, "10.10.12.2", "10.10.13.2"),
    ("r3", REDE_DESTINO, "10.10.34.2", "10.10.35.2"),
    ("r3", REDE_ORIGEM,  "10.10.23.1", "10.10.13.1"),
    ("r5", REDE_ORIGEM,  "10.10.45.1", "10.10.35.1"),
]

INTERVALO_MONITORAMENTO_S = 1
LIMIAR_FALHAS = 3
LIMIAR_SUCESSOS = 3
TIMEOUT_PING_S = 1

# Ping contínuo usado para medir perdas durante a convergência.
INTERVALO_TRAFEGO_S = 0.2
