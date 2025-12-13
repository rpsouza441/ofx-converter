# OFX to QIF Converter v3.0

Conversor automático de arquivos OFX para QIF usando Docker, otimizado para ezBookkeeping.

**Novo v3.0:** Arquitetura modular com categorização configurável via YAML!

## Estrutura do Projeto

```
ofx-converter/
├── ofx_converter.py           # Main - orquestra services
├── services/                  # Services modulares
│   ├── file_reader.py        # Leitura OFX (auto-detecção encoding)
│   ├── date_extractor.py     # Extração de mês-ano
│   ├── text_normalizer.py    # Normalização UTF-8
│   ├── categorizer.py        # Categorização de transações
│   └── qif_writer.py         # Escrita de QIF
├── categorias.yaml           # Regras de categorização (editável!)
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## Como usar

### 1. Configuração inicial
```bash
chmod +x setup.sh
./setup.sh
```

### 2. Iniciar o conversor
```bash
docker compose up -d
```

### 3. Usar o conversor
1. Coloque arquivos `.ofx` na pasta `./entrada/`
2. O conversor processa automaticamente (verifica a cada 5 segundos)
3. Arquivos convertidos `.qif` ficam em `./convertido/`
4. Arquivos processados são movidos para `./entrada/lido/`

### 4. Ver logs
```bash
docker compose logs -f
```

### 5. Parar o conversor
```bash
docker compose down
```

## Funcionalidades v3.0

### Arquitetura Modular 
- **Services separados** para cada responsabilidade
- **Fácil manutenção** e extensão
- **Testável** (cada service pode ser testado independentemente)

### Categorização Configurável 
- **Arquivo YAML** com regras de categorização
- **Adicionar categorias SEM alterar código Python!**
- Suporte a múltiplas palavras-chave por categoria

### Monitoramento Automático 
- Monitoramento da pasta entrada
- Conversão OFX → QIF automática
- Organização por mês-ano

### Categorização Inteligente 
- Dividendos/Proventos → "Dividendos"
- Salário → "Salário"
- PIX/TED recebidos → "Receitas"
- PIX/TED enviados → "Transferências"
- Boletos → "Boletos"
- Alimentação, Saúde, Combustível, etc.

### Tratamento de Dados 
- **Normalização UTF-8** (remove acentos automaticamente)
- **Correção de datas malformadas** (anos inválidos)
- **Data mais frequente** para organização de pastas
- **Permissões corretas** (rw-rw-r--)

## Adicionar/Editar Categorias

Edite o arquivo `categorias.yaml`:

```yaml
receitas:
  - categoria: Freelance
    palavras:
      - freelance
      - servico prestado
      - consultoria

despesas:
  - categoria: Streaming
    palavras:
      - netflix
      - spotify
      - amazon prime
```

Rebuild Docker:

```bash
docker compose down
docker compose build
docker compose up -d
```

Pronto! Suas categorias estão ativas.

## Configurações

Variáveis de ambiente no `docker-compose.yml`:

- `WATCH_INTERVAL`: Intervalo de verificação em segundos (padrão: 5)
- `TZ`: Fuso horário (padrão: America/Sao_Paulo)

## Estrutura de Pastas

```
ofx-converter/
├── entrada/           <- Coloque arquivos .ofx aqui
│   └── lido/         <- Arquivos já processados (organizados por mês)
│       ├── 10-2025/
│       └── 11-2025/
├── convertido/       <- Arquivos .qif prontos (organizados por mês)
│   ├── 10-2025/
│   └── 11-2025/
└── logs/            <- Logs da aplicação
```

## Troubleshooting

### Container não inicia
```bash
docker compose logs
```

### Arquivos não são processados
- Verifique se os arquivos têm extensão `.ofx` ou `.qfx`
- Verifique permissões das pastas
- Veja logs: `docker compose logs -f`

### Problema de encoding
O conversor tenta múltiplos encodings (UTF-8, latin-1, cp1252) automaticamente.

### Datas inválidas
Datas malformadas (ex: ano 0002) são automaticamente corrigidas para o ano atual.

### Categorias não aplicadas
- Verifique o arquivo `categorias.yaml`
- Rebuild: `docker compose down && docker compose build && docker compose up -d`
- Veja logs para erros

## Atualizar

```bash
docker compose down
docker compose build --no-cache
docker compose up -d
```

## Desenvolvimento

### Executar localmente (sem Docker)

```bash
# Instalar dependências
pip install ofxparse pyyaml

# Executar
python ofx_converter.py
```

### Testar Services

```python
from services.categorizer import TransactionCategorizer

categorizer = TransactionCategorizer('categorias.yaml')
categoria = categorizer.categorize("Salario ord empregador", 1500.00)
print(categoria)  # Saída: Salário
```

## Versões

- **v3.0** - Arquitetura modular com services + categorização via YAML
- **v2.0** - Organização por mês-ano + correção de datas
- **v1.0** - Versão inicial

## Licença

MIT
