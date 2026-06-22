---
name: ofx-converter
version: 3.0.0
language: Python 3.11
runtime: Docker
---

# ofx-converter

Conversor de extratos bancarios (OFX/CSV/XLSX/PDF) para formato CSV do EZBookkeeping.
Roda em Docker com watch mode — monitora pasta `entrada/` e converte automaticamente.

## Stack
- Python 3.11
- Docker (docker-compose)
- ofxparse / xml parsing para OFX
- openpyxl para XLSX (Rico/XP investimentos)
- Sem framework de teste configurado ainda

## Fontes Suportadas
- Banco do Brasil (OFX via bb_parser)
- Nubank (OFX via ofx_parser)
- Inter (OFX via ofx_parser)
- XP Conta Digital (OFX via xp_conta_parser)
- XP Cartao de Credito (CSV via xp_cc_parser)
- Rico Conta Digital (OFX via rico_parser)
- Rico Investimentos (XLSX via rico_investimento_parser)
- Mercado Pago (CSV via mercadopago_parser — PRECISA MIGRAR PARA PDF)

## Arquitetura (v3.0 — services + processors)
- `ofx_converter.py` — entry point, inicializa services e roda watch loop
- `services/` — parsers e services individuais
- `services/processors/` — adaptadores que conectam parsers ao pipeline
- `services/processor_registry.py` — resolve qual processor usar por arquivo
- `services/conversion_pipeline.py` — pipeline: parse -> postprocess -> write CSV -> move input
- `categorias.yaml` — regras de categorizacao por keyword
- `contas.yaml` — mapeamento arquivo -> conta no EZBookkeeping

## Fluxo
1. Watch monitora `entrada/`
2. ProcessorRegistry detecta o tipo do arquivo
3. Processor.parse() extrai transacoes
4. Pipeline aplica postprocessor, escreve CSV, move arquivo para `entrada/lido/MM-YYYY/`
5. Output vai para `convertido/MM-YYYY/`

## Uso
- Pessoal (Rodrigo + Carine), mensal
- Dados sensiveis em samples/ e entrada/ (.gitignore)
- Docker: `docker-compose up`
