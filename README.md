# OFX to ezBookkeeping CSV Converter

Conversor automático de exports bancários para CSV de importação do ezBookkeeping usando Docker.

O container monitora `./entrada`, detecta arquivos suportados, escolhe um processor, parseia transações, aplica categorização e pós-processamento, identifica a conta pelo nome do arquivo, gera CSV ezBookkeeping e move o arquivo original para `./entrada/lido/<mes-ano>/`.

## Formatos Suportados

- OFX/QFX
- Mercado Pago CSV
- Rico CSV
- Rico/XP investimento XLSX
- XP cartão CSV
- XP conta digital CSV
- Banco do Brasil CSV

## Arquitetura

```text
ofx_converter.py
  Entry point, bootstrap de dependências, watch loop e wrappers de compatibilidade.

services/processor_registry.py
  Escolhe o processor correto para cada arquivo.

services/processors/
  Adaptadores por banco/formato. Detectam arquivo e chamam parsers existentes.

services/conversion_pipeline.py
  Fluxo comum: parse -> mês -> conta -> pós-processamento -> CSV -> mover para lido.

services/transaction_postprocessor.py
  Ajustes após parse, como regra de pagamento recebido em CC Nubank.

services/*_parser.py
  Parsers reais de cada banco/formato.

services/ezbookkeeping_csv_writer.py
  Escrita do CSV compatível com ezBookkeeping.
```

Documentação complementar:

- [MELHORIA_ARQUITETURA.md](MELHORIA_ARQUITETURA.md)
- [UML_ARQUITETURA_FINAL.md](UML_ARQUITETURA_FINAL.md)
- [ARQUITETURA_CONVERSOR_OFX.md](ARQUITETURA_CONVERSOR_OFX.md)

## Estrutura do Projeto

```text
ofx-converter/
├── ofx_converter.py
├── services/
│   ├── conversion_pipeline.py
│   ├── processor_registry.py
│   ├── transaction_postprocessor.py
│   ├── processors/
│   ├── *_parser.py
│   ├── categorizer.py
│   ├── account_matcher.py
│   ├── date_extractor.py
│   └── ezbookkeeping_csv_writer.py
├── categorias.yaml
├── contas.yaml
├── Dockerfile
├── docker-compose.yml
└── setup.sh
```

## Como Usar

### 1. Preparar pastas

```bash
chmod +x setup.sh
./setup.sh
```

O `setup.sh` cria as pastas locais usadas pelo compose:

```text
./entrada
./entrada/lido
./convertido
./logs
```

### 2. Subir o container

```bash
docker compose up -d
```

### 3. Processar arquivos

Coloque arquivos suportados em:

```text
./entrada/
```

O conversor verifica a pasta a cada `WATCH_INTERVAL` segundos. Quando um arquivo é convertido:

- CSV final vai para `./convertido/<mes-ano>/`
- arquivo original vai para `./entrada/lido/<mes-ano>/`
- logs ficam em `./logs/`

### 4. Ver logs

```bash
docker compose logs -f
```

### 5. Parar

```bash
docker compose down
```

## Mapeamento Docker

O `docker-compose.yml` monta arquivos/pastas do host dentro do container:

```text
Host                  Container
./entrada             /app/entrada
./entrada/lido        /app/entrada/lido
./convertido          /app/convertido
./logs                /app/logs
./ofx_converter.py    /app/ofx_converter.py
./services            /app/services
./categorias.yaml     /app/categorias.yaml
./contas.yaml         /app/contas.yaml
```

Por isso mudanças em `ofx_converter.py`, `services/`, `categorias.yaml` e `contas.yaml` são montadas no container. Para dependências ou Dockerfile, faça rebuild.

## Rebuild no Selfhosted

```bash
cd /srv/DATA/ofx-converter
docker compose down
docker compose build --no-cache
docker compose up -d
docker compose logs -f
```

## Testar Depois do Rebuild

Verifique container:

```bash
docker compose ps
docker compose logs -f ofx-converter
```

Valide sintaxe dentro do container:

```bash
docker compose exec ofx-converter python -m py_compile /app/ofx_converter.py /app/services/*.py /app/services/processors/*.py
```

Teste conversão com cópia de um arquivo pequeno em `./entrada/`. Depois confira:

```text
./convertido/<mes-ano>/
./entrada/lido/<mes-ano>/
./logs/
```

## Atualizar Categorias

Edite `categorias.yaml`:

```yaml
receitas:
  - categoria: Freelance
    subcategoria: Serviços
    palavras:
      - freelance
      - servico prestado

despesas:
  - categoria: Streaming
    subcategoria: Assinaturas
    palavras:
      - netflix
      - spotify
```

Depois reinicie:

```bash
docker compose restart
```

## Atualizar Contas

Edite `contas.yaml` para ajustar identificação de conta pelo nome do arquivo. O `AccountMatcher` usa palavras-chave de titular, banco e tipo para escolher a conta ezBookkeeping.

Depois reinicie:

```bash
docker compose restart
```

## Configurações

Variáveis em `docker-compose.yml`:

- `WATCH_INTERVAL`: intervalo de varredura em segundos. Padrão: `5`.
- `TZ`: timezone do container. Padrão: `America/Sao_Paulo`.

Variáveis opcionais de ownership:

- `FILE_CHOWN_ENABLED=true`
- `FILE_CHOWN_UID=1000`
- `FILE_CHOWN_GID=1000`

## Troubleshooting

### Container não inicia

```bash
docker compose logs
```

### Arquivo não processa

- Confirme se o arquivo está em `./entrada/`.
- Confirme se o formato é suportado.
- Veja logs com `docker compose logs -f`.
- Verifique se o processor detecta por header ou nome de arquivo.

### CSV não aparece

- Veja `./logs/`.
- Confirme se o arquivo original foi movido para `./entrada/lido/<mes-ano>/`.
- Se não foi movido, houve erro antes da finalização.

### Dependências Python

O Dockerfile instala:

```text
ofxparse
pyyaml
openpyxl
```

Se rodar local sem Docker, instale:

```bash
pip install ofxparse pyyaml openpyxl
```

## Desenvolvimento

Rodar localmente:

```bash
python3 ofx_converter.py
```

Checar sintaxe:

```bash
PYTHONPYCACHEPREFIX=/tmp/ofx_converter_pycache python3 -m py_compile ofx_converter.py services/*.py services/processors/*.py
```

Antes de commit:

```bash
git status --short
git diff --stat
```

Evite commitar dados sensíveis de `entrada/`, `convertido/`, `logs/`, `.recycle/` e backups locais.

## Versões

- Arquitetura atual: pipeline comum + registry + processors por banco/formato.
- v3.0: services modulares + categorização via YAML.
- v2.0: organização por mês-ano + correção de datas.
- v1.0: versão inicial.

## Licença

MIT
