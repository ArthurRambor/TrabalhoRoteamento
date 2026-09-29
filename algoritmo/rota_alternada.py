#!/usr/bin/env python3
"""
rota_alternada.py — algoritmo "Rota Alternada por Falha"
(implementação da proposta descrita na seção 8 do relatório de andamento)

Caminho principal:      R1 -> R2 -> R3 -> R4 -> R5
Caminho alternativo:    R1 -> R3 -> R5  (diagonais)

Funcionamento (igual ao "Funcionamento proposto" do relatório):
  1. Monitora periodicamente, via ping, a disponibilidade do próximo salto
     do caminho principal (R1 -> R2).
  2. Após LIMIAR_FALHAS verificações consecutivas sem resposta, considera o
     caminho principal indisponível e aplica as rotas alternativas nos
     roteadores envolvidos (R1, R3 e R5 — R2 e R4 não são tocados).
  3. Após LIMIAR_SUCESSOS verificações consecutivas bem-sucedidas do caminho
     principal, retorna às rotas principais.
  4. Registra: horário de falha, detecção, alteração de rota, recuperação,
     perda de pacotes e número de mudanças — tudo em resultados/eventos.csv.

A troca de rota é feita via vtysh (rota estática do FRR), não via `ip route`
direto no kernel, para ficar consistente com o restante do ambiente (que já
é gerenciado pelo FRR) e evitar que o zebra reconcilie/ignore uma rota
inserida por fora dele.

Uso:
    python3 algoritmo/rota_alternada.py                # monitoramento contínuo
    python3 algoritmo/rota_alternada.py --dry-run       # mostra os comandos, não executa
    python3 algoritmo/rota_alternada.py --once-status   # testa o link uma vez e sai

Rode a partir da raiz do projeto (~/trabalho-roteamento), para que os logs
caiam em resultados/eventos.csv como esperado pela estrutura de pastas do
relatório.
"""

import argparse
import csv
import os
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone

from config_topologia import (
    CONTAINERS,
    HOST_A_IP,
    HOST_B_IP,
    INTERVALO_MONITORAMENTO_S,
    INTERVALO_TRAFEGO_S,
    LIMIAR_FALHAS,
    LIMIAR_SUCESSOS,
    MONITOR_FROM,
    MONITOR_TARGET_IP,
    ROTAS,
    TIMEOUT_PING_S,
)

LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "resultados")
LOG_FILE = os.path.join(LOG_DIR, "eventos.csv")

# Contadores globais do probe de tráfego (host-a -> host-b), protegidos por lock.
_trafego_lock = threading.Lock()
_trafego_enviados = 0
_trafego_recebidos = 0
_trafego_ativo = True

_numero_mudancas = 0

# ----------------------------------------------------------------------------
# Utilidades
# ----------------------------------------------------------------------------


def agora_iso():
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="milliseconds")


def garantir_log():
    os.makedirs(LOG_DIR, exist_ok=True)
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w", newline="") as f:
            csv.writer(f).writerow(
                ["timestamp", "evento", "detalhe", "perda_pacotes_janela", "numero_mudancas"]
            )


def registrar_evento(evento: str, detalhe: str = "", perda_pacotes: str = "", numero_mudancas: str = ""):
    garantir_log()
    with open(LOG_FILE, "a", newline="") as f:
        csv.writer(f).writerow([agora_iso(), evento, detalhe, perda_pacotes, numero_mudancas])
    print(f"[{agora_iso()}] {evento} - {detalhe}")


def docker_exec(container_key: str, comando: list, dry_run: bool = False):
    container = CONTAINERS[container_key]
    full_cmd = ["docker", "exec", container] + comando
    if dry_run:
        print(f"[dry-run] {' '.join(full_cmd)}")
        return 0, ""
    resultado = subprocess.run(full_cmd, capture_output=True, text=True)
    return resultado.returncode, (resultado.stdout + resultado.stderr).strip()


def ping_ok(container_key: str, ip_destino: str) -> bool:
    codigo, _ = docker_exec(
        container_key, ["ping", "-c", "1", "-W", str(TIMEOUT_PING_S), ip_destino]
    )
    return codigo == 0


# ----------------------------------------------------------------------------
# Troca de rota via FRR (vtysh) — só em R1, R3 e R5
# ----------------------------------------------------------------------------


def aplicar_rota_estatica(router: str, rede: str, via_nova: str, via_antiga: str, dry_run: bool = False):
    """Substitui uma rota estática e informa se o comando foi aceito."""
    comandos_vtysh = [
        "configure terminal",
        f"no ip route {rede} {via_antiga}",
        f"ip route {rede} {via_nova}",
        "end",
    ]
    args = ["vtysh"]
    for comando in comandos_vtysh:
        args += ["-c", comando]

    codigo, saida = docker_exec(router, args, dry_run=dry_run)
    if codigo != 0 and not dry_run:
        registrar_evento(
            "ERRO_ROTA",
            f"{router}: falha ao trocar rota {rede}: {saida}",
        )
    return codigo == 0


def _executar_troca(rotas, dry_run: bool = False):
    """Aplica as rotas em sequência e tenta reverter alterações parciais."""
    inicio = time.monotonic()
    aplicadas = []

    for router, rede, principal, alternativa in rotas:
        if not aplicar_rota_estatica(
            router,
            rede,
            via_nova=alternativa,
            via_antiga=principal,
            dry_run=dry_run,
        ):
            registrar_evento(
                "TROCA_ABORTADA",
                f"Falha em {router} para {rede}; iniciando reversão.",
            )
            for r, n, p, a in reversed(aplicadas):
                if not aplicar_rota_estatica(
                    r, n, via_nova=p, via_antiga=a, dry_run=dry_run
                ):
                    registrar_evento(
                        "ERRO_REVERSAO",
                        f"Não foi possível reverter {r}, rede {n}.",
                    )
            return False, (time.monotonic() - inicio) * 1000

        aplicadas.append((router, rede, principal, alternativa))

    return True, (time.monotonic() - inicio) * 1000


def trocar_para_alternativa(dry_run: bool = False):
    global _numero_mudancas
    sucesso, duracao_ms = _executar_troca(ROTAS, dry_run=dry_run)
    if sucesso:
        _numero_mudancas += 1
    return sucesso, duracao_ms


def restaurar_principal(dry_run: bool = False):
    global _numero_mudancas
    rotas_reversas = [
        (router, rede, alternativa, principal)
        for router, rede, principal, alternativa in ROTAS
    ]
    sucesso, duracao_ms = _executar_troca(rotas_reversas, dry_run=dry_run)
    if sucesso:
        _numero_mudancas += 1
    return sucesso, duracao_ms


# ----------------------------------------------------------------------------
# Probe de tráfego (host-a -> host-b): só mede perda de pacotes, não decide nada
# ----------------------------------------------------------------------------


def thread_trafego(dry_run: bool = False):
    global _trafego_enviados, _trafego_recebidos
    if dry_run:
        return  # em dry-run não há containers reais para pingar
    while _trafego_ativo:
        with _trafego_lock:
            _trafego_enviados += 1
        if ping_ok("host-a", HOST_B_IP):
            with _trafego_lock:
                _trafego_recebidos += 1
        time.sleep(INTERVALO_TRAFEGO_S)


def snapshot_trafego():
    with _trafego_lock:
        return _trafego_enviados, _trafego_recebidos


# ----------------------------------------------------------------------------
# Loop principal de monitoramento (detecção de falha + histerese)
# ----------------------------------------------------------------------------


def monitorar(dry_run: bool = False):
    estado_ativo = "principal"
    falhas_consecutivas = 0
    sucessos_consecutivos = 0

    registrar_evento(
        "INICIO_MONITORAMENTO",
        f"alvo={MONITOR_TARGET_IP} de={MONITOR_FROM} intervalo={INTERVALO_MONITORAMENTO_S}s "
        f"limiar={LIMIAR_FALHAS}/{LIMIAR_SUCESSOS} dry_run={dry_run}",
    )

    enviados_ref, recebidos_ref = snapshot_trafego()

    try:
        while True:
            ok = ping_ok(MONITOR_FROM, MONITOR_TARGET_IP) if not dry_run else False

            if ok:
                sucessos_consecutivos += 1
                falhas_consecutivas = 0
            else:
                falhas_consecutivas += 1
                sucessos_consecutivos = 0

            if estado_ativo == "principal" and falhas_consecutivas >= LIMIAR_FALHAS:
                registrar_evento(
                    "FALHA_DETECTADA",
                    f"{falhas_consecutivas} verificações sem resposta em {MONITOR_TARGET_IP}",
                )

                sucesso, duracao_ms = trocar_para_alternativa(dry_run=dry_run)

                if sucesso:
                    enviados_atual, recebidos_atual = snapshot_trafego()
                    perdidos = (enviados_atual - enviados_ref) - (recebidos_atual - recebidos_ref)
                    registrar_evento(
                        "ROTA_TROCADA",
                        f"principal -> alternativa ({duracao_ms:.1f} ms)",
                        perda_pacotes=str(max(perdidos, 0)),
                        numero_mudancas=str(_numero_mudancas),
                    )
                    enviados_ref, recebidos_ref = enviados_atual, recebidos_atual
                    estado_ativo = "alternativa"
                    falhas_consecutivas = 0
                else:
                    registrar_evento(
                        "ERRO_TROCA_ROTA",
                        "não foi possível aplicar a rota alternativa; estado mantido em principal",
                        numero_mudancas=str(_numero_mudancas),
                    )
                    falhas_consecutivas = 0

            elif estado_ativo == "alternativa" and sucessos_consecutivos >= LIMIAR_SUCESSOS:
                registrar_evento(
                    "RECUPERACAO_DETECTADA",
                    f"{sucessos_consecutivos} verificações OK consecutivas em {MONITOR_TARGET_IP}",
                )

                sucesso, duracao_ms = restaurar_principal(dry_run=dry_run)

                if sucesso:
                    enviados_atual, recebidos_atual = snapshot_trafego()
                    perdidos = (enviados_atual - enviados_ref) - (recebidos_atual - recebidos_ref)
                    registrar_evento(
                        "ROTA_RESTAURADA",
                        f"alternativa -> principal ({duracao_ms:.1f} ms)",
                        perda_pacotes=str(max(perdidos, 0)),
                        numero_mudancas=str(_numero_mudancas),
                    )
                    enviados_ref, recebidos_ref = enviados_atual, recebidos_atual
                    estado_ativo = "principal"
                    sucessos_consecutivos = 0
                else:
                    registrar_evento(
                        "ERRO_RESTAURACAO_ROTA",
                        "não foi possível restaurar a rota principal; estado mantido em alternativa",
                        numero_mudancas=str(_numero_mudancas),
                    )
                    sucessos_consecutivos = 0

            time.sleep(INTERVALO_MONITORAMENTO_S)

    except KeyboardInterrupt:
        registrar_evento(
            "FIM_MONITORAMENTO",
            f"interrompido pelo usuário (estado={estado_ativo})",
            numero_mudancas=str(_numero_mudancas),
        )


# ----------------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------------


def main():
    global _trafego_ativo

    parser = argparse.ArgumentParser(description='Algoritmo "Rota Alternada por Falha"')
    parser.add_argument("--dry-run", action="store_true", help="mostra os comandos previstos sem executá-los")
    parser.add_argument("--once-status", action="store_true", help="testa o link uma vez e sai")
    args = parser.parse_args()

    if args.once_status:
        ok = ping_ok(MONITOR_FROM, MONITOR_TARGET_IP)
        print("UP" if ok else "DOWN")
        sys.exit(0 if ok else 1)

    if args.dry_run:
        print("\n=== SIMULAÇÃO: aplicação das rotas alternativas ===")
        for router, rede, principal, alternativa in ROTAS:
            aplicar_rota_estatica(
                router, rede, via_nova=alternativa,
                via_antiga=principal, dry_run=True
            )

        print("\n=== SIMULAÇÃO: restauração das rotas principais ===")
        for router, rede, principal, alternativa in ROTAS:
            aplicar_rota_estatica(
                router, rede, via_nova=principal,
                via_antiga=alternativa, dry_run=True
            )

        print("\nSimulação concluída. Nenhum comando foi executado na rede.")
        return

    t = threading.Thread(target=thread_trafego, daemon=True)
    t.start()

    try:
        monitorar(dry_run=False)
    finally:
        _trafego_ativo = False


if __name__ == "__main__":
    main()
