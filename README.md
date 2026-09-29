# Comparação de Métodos de Roteamento

## 1. Objetivo

Este projeto compara diferentes métodos de roteamento em uma rede simulada, utilizando cinco roteadores e múltiplos caminhos entre as redes.

São avaliados:

* O protocolo OSPF;
* O protocolo RIP;
* Um algoritmo próprio de seleção e alternância de rotas.

O objetivo é observar o comportamento dos cenários e comparar métricas de roteamento, tráfego de controle, latência e recuperação de falhas.

## 2. Ambiente

* Sistema operacional: Ubuntu 26.04.1 LTS no WSL2
* Docker Engine: 29.1.3
* Containerlab: 0.79.0
* Roteadores: FRRouting (FRR)
* Hosts: Alpine Linux
* Linguagem do algoritmo: Python

## 3. Estrutura do projeto

```text
trabalho-roteamento/
├── topologia/
│   ├── topologia.clab.yml
│   ├── topologia-rip.clab.yml
│   └── topologia-algoritmo.clab.yml
├── configuracoes/
│   ├── ospf/
│   ├── rip/
│   └── algoritmo/
├── algoritmo/
├── testes/
├── resultados/
├── graficos/
├── backup/
├── video/
├── publicacao/
└── README.md
```

## 4. Cenários

Os cenários são executados em laboratórios separados, evitando que os protocolos sejam executados simultaneamente.

| Cenário           | Arquivo de topologia                     |
| ----------------- | ---------------------------------------- |
| OSPF              | `topologia/topologia.clab.yml`           |
| RIP               | `topologia/topologia-rip.clab.yml`       |
| Algoritmo próprio | `topologia/topologia-algoritmo.clab.yml` |

Cada cenário utiliza cinco roteadores e múltiplos caminhos na topologia.

## 5. Execução

A partir da pasta principal do projeto, implante o cenário desejado.

### OSPF

```bash
sudo containerlab deploy --topo topologia/topologia.clab.yml
```

### RIP

```bash
sudo containerlab deploy --topo topologia/topologia-rip.clab.yml
```

### Algoritmo próprio

```bash
sudo containerlab deploy --topo topologia/topologia-algoritmo.clab.yml
```

Para verificar os laboratórios:

```bash
sudo containerlab inspect --all
docker ps
```

## 6. Algoritmo próprio

O algoritmo monitora a conectividade e realiza a alternância entre uma rota principal e uma rota alternativa, conforme os limiares configurados de falhas e sucessos consecutivos.

Após a recuperação da conectividade, o algoritmo pode restaurar a rota principal.

Os parâmetros de monitoramento e os comandos de configuração estão nos arquivos do diretório `algoritmo/` e nas configurações correspondentes.

## 7. Resultados e métricas

Os resultados são armazenados no diretório `resultados/`, incluindo métricas de roteamento, capturas de tráfego e registros dos testes.

Os gráficos são gerados pelos scripts do diretório `graficos/`.

As métricas consideradas incluem:

* Quantidade de rotas e entradas na tabela de encaminhamento;
* Pacotes e bytes de controle observados;
* Taxa de tráfego de controle;
* Latência e perda de pacotes;
* Tempo de troca e restauração de rotas.

As capturas de OSPF e RIP foram realizadas na interface `eth1` do roteador R1, durante janelas de 60 segundos. Portanto, representam observações daquela interface e período, não o tráfego total da rede. Os tipos de pacotes capturados também diferem entre os protocolos.

Os tempos de troca e restauração foram medidos nos ensaios do algoritmo próprio. Não devem ser interpretados como uma comparação direta de failover com OSPF e RIP.

## 8. Reprodutibilidade

### 8.1. Preparação

Certifique-se de que o ambiente possui WSL2, Docker, Containerlab, Python 3 e Matplotlib instalados.

Acesse a pasta principal do projeto:

```bash
cd ~/trabalho-roteamento
```

### 8.2. Implantação dos cenários

Implante somente o laboratório que será testado:

**OSPF**

```bash
sudo containerlab deploy --topo topologia/topologia.clab.yml
```

**RIP**

```bash
sudo containerlab deploy --topo topologia/topologia-rip.clab.yml
```

**Algoritmo próprio**

```bash
sudo containerlab deploy --topo topologia/topologia-algoritmo.clab.yml
```

Verifique os contêineres:

```bash
sudo containerlab inspect --all
docker ps
```

### 8.3. Teste do algoritmo próprio

Com o laboratório do algoritmo implantado, verifique o enlace monitorado:

```bash
python3 algoritmo/rota_alternada.py --once-status
```

O resultado `UP` indica conectividade com o destino monitorado; `DOWN` indica falha na verificação.

Para visualizar os comandos de alternância e restauração sem modificar as rotas:

```bash
python3 algoritmo/rota_alternada.py --dry-run
```

Para iniciar o monitoramento contínuo:

```bash
python3 algoritmo/rota_alternada.py
```

Interrompa o monitoramento com `Ctrl+C`. A execução contínua pode modificar as rotas dos roteadores; deve ser realizada durante um ensaio controlado, com o laboratório do algoritmo ativo.

### 8.4. Geração dos gráficos

Com os arquivos CSV de resultados disponíveis, execute:

```bash
python3 graficos/gerar_graficos.py
python3 graficos/gerar_graficos_comparativos.py
```

Os gráficos são salvos no diretório `graficos/`.

### 8.5. Resultados

Os arquivos de resultados e as capturas de tráfego ficam no diretório `resultados/`. A análise comparativa está disponível em `resultados/analise_comparativa.txt`.

As medições são experimentais e dependem da topologia, das condições de execução e dos procedimentos de coleta descritos neste projeto. As capturas de tráfego representam apenas a interface e o intervalo monitorados.


## 9. Autoria

**Autores:** Arthur Rambor e Silva e Leonardo Taborda Pinto.

**Instituição e disciplina:** Unisinos - Redes de Computadores: Internetworking, Roteamento e Transmissão.
