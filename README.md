# OFX/CSV Multi-Format to ezBookkeeping Converter v5.0

Conversor automático de múltiplos formatos financeiros para ezBookkeeping (CSV + QIF).

**Formatos Suportados:**
- OFX/QFX (bancos brasileiros)
- Mercado Pago CSV
- Rico Corretora CSV (conta digital)
- Rico Investimentos XLSX (conta investimento)
- XP Cartão de Crédito CSV

**Novidades v5.0:**
- Suporte completo a XP Cartão de Crédito CSV
- Categorização totalmente alinhada com ezBookkeeping
- Detecção automática por header (BOM-safe)
- Formatação inteligente de parcelas
- 100% das categorias e subcategorias do ezBookkeeping

---

## Funcionalidades

### Formatos Suportados

**Entrada:**
- Arquivos OFX/QFX (bancos brasileiros)
- CSV Mercado Pago (conta digital)
- CSV Rico (conta digital)
- XLSX Rico Investimentos (conta investimento)
- CSV XP Cartão de Crédito

**Saída:**
- CSV ezBookkeeping (formato nativo, recomendado)
- QIF (compatibilidade com outros apps)

### Categorização Automática

**100% Configurável via YAML** - sem código Python!

**Estrutura ezBookkeeping completa:**

Receitas: Ganhos Ocupacionais, Finanças & Investimento, Diversos
- Ganhos Ocupacionais: Renda de Salário, Renda de Bônus, Pagamento de Hora Extra, Renda de Trabalho Paralelo, Estorno
- Finanças & Investimento: Renda de Investimento, Renda de Aluguel, Rendimento de Juros
- Diversos: Renda de Presente e Dinheiro da Sorte, Renda de Prêmios, Ganho Extraordinário, Outras Receitas, Reembolso

Despesas: Comida e Bebida, Vestuário e Aparência, Moradia e Utensílios Domésticos, Transporte, Comunicação, Entretenimento, Educação & Estudos, Presentes & Doações, Médico & Saúde, Finanças & Seguro, Diversos

Transferências: Transferência Geral, Empréstimo e Dívida, Diversos
- Transferência Geral: Transferência Bancária, Pagamento de Cartão de Crédito, Depósitos e Saques

**Exemplos:**
```
Rendimentos                         → Finanças & Investimento > Rendimento de Juros
WELLHUB GYMPASS BR                  → Entretenimento > Esporte & Fitness
Pagamento de fatura                 → Diversos > Outras Despesas (ajustar manualmente)
PETLOVE*CLUBE                       → Entretenimento > Despesa com Animais de Estimação
Transacao Pix enviada Carine        → Transferência Geral > Transferência Bancária
```

### Automação

- Monitora pasta `entrada/` a cada 5 segundos
- Conversão automática OFX/CSV → CSV + QIF
- Organização automática por mês-ano
- Logs detalhados

---

## Estrutura do Projeto

```
ofx-converter/
├── ofx_converter.py              # Orquestrador principal
├── services/                     # Serviços modulares
│   ├── mercadopago_parser.py    # Parser Mercado Pago CSV
│   ├── rico_parser.py            # Parser Rico CSV (conta digital)
│   ├── rico_investimento_parser.py  # Parser Rico XLSX (investimentos)
│   ├── xp_cartao_parser.py       # Parser XP Cartão CSV
│   ├── ofx_parser.py             # Parser OFX
│   ├── categorizer.py            # Categorização via YAML
│   ├── ezbookkeeping_csv_writer.py  # Gerador CSV ezBookkeeping
│   ├── qif_writer.py             # Gerador QIF
│   ├── file_reader.py            # Leitura multi-encoding
│   ├── date_extractor.py         # Extração de datas
│   └── text_normalizer.py       # Normalização UTF-8
├── categorias.yaml               # Regras de categorização (EDITÁVEL)
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## Como Usar

### 1. Configuração Inicial

```bash
chmod +x setup.sh
./setup.sh
```

### 2. Iniciar o Conversor

```bash
docker-compose up -d
```

### 3. Converter Arquivos

#### Mercado Pago CSV
```bash
# Copiar arquivo para entrada/
cp account_statement_xxxxx.csv entrada/mercadopago-11-2025.csv

# Aguardar conversão automática (5 segundos)
# Arquivos gerados em convertido/MM-YYYY/:
#   - mercadopago-11-2025.csv  (ezBookkeeping)
#   - mercadopago-11-2025.qif  (compatibilidade)
```

#### OFX/QFX (Bancos)
```bash
# Copiar arquivo para entrada/
cp extrato_nubank.ofx entrada/

# Arquivos gerados em convertido/MM-YYYY/
# - extrato_nubank.csv  (ezBookkeeping)
# - extrato_nubank.qif  (compatibilidade)
```

#### Rico CSV (Conta Digital)
```bash
# Copiar CSV da Rico para entrada/
cp Rico_carine_extrato_de_01-11-2025_ate_30-11-2025.csv entrada/

# Detecção automática pelo nome "rico"
# Arquivos gerados em convertido/MM-YYYY/
```

#### Rico XLSX (Investimentos)
```bash
# Copiar XLSX de investimentos para entrada/
cp Rico_investimento_Carine_extrato_de_01-11-2025_ate_30-11-2025.xlsx entrada/

# Detecção automática por "rico" + "investimento" no nome
# Usa data de liquidação (quando $ movimenta)
# Arquivos gerados em convertido/MM-YYYY/
```

#### XP Cartão de Crédito CSV
```bash
# Copiar CSV de fatura XP para entrada/
cp Fatura_XP_CC_2025-11-15.csv entrada/

# Detecção automática pelo header (Data;Estabelecimento;Portador;Valor;Parcela)
# Descrições formatadas: "PORTADOR - ESTABELECIMENTO (parcela X/Y)"
# Datas convertidas: DD/MM/YYYY → YYYY-MM-DD HH:MM:SS
# BOM handling automático (UTF-8 with signature)
# Arquivos gerados em convertido/MM-YYYY/
```

### 4. Importar no ezBookkeeping

1. Abra ezBookkeeping
2. Vá em **Importar Dados**
3. Selecione o arquivo `.csv` gerado
4. **Preencha Account/Account2** para transferências durante importação
5. Pronto! Categorias e subcategorias já estarão aplicadas

### 5. Ver Logs

```bash
docker-compose logs -f
```

### 6. Parar o Conversor

```bash
docker-compose down
```

---

## Configuração de Categorias

### Estrutura do `categorias.yaml`

```yaml
# Receitas com subcategorias
receitas:
  - categoria: Renda de Investimento
    subcategoria: Rendimento de Juros
    palavras:
      - rendimento
      - rendimentos
      - dividendo

# Despesas com subcategorias
despesas:
  - categoria: Compras
    subcategoria: Compras Online
    palavras:
      - pagamento com qr pix amazon
      - marketplace

# Transferências (frases completas!)
transferencias:
  - categoria: Transferência Geral
    subcategoria: Transferência Bancária
    palavras:
      - transacao pix enviada
      - transacao pix recebida
      - transferencia pix enviada
```

### Como Adicionar Novas Transferências

**Use frases completas para evitar falsos positivos:**

```yaml
transferencias:
  - categoria: Transferência Geral
    subcategoria: Transferência Bancária
    palavras:
      # Adicione aqui pessoas específicas que você transfere:
      - transacao pix enviada maria silva
      - transacao pix recebida joao santos
      - transferencia nubank recebida pedro
```

### Como Adicionar Novas Categorias

```yaml
despesas:
  - categoria: Saúde
    subcategoria: Academia
    palavras:
      - smart fit
      - bodytech
      - mensalidade academia
```

### Aplicar Mudanças

```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

---

## Exemplos de Categorização

### Transferências (Type: Transfer)
```
Descrição                                → Categoria              → Subcategoria
===============================================================================
Transacao Pix recebida Rodrigo          → Transferência Geral    → Transferência Bancária
Transacao Pix enviada Carine            → Transferência Geral    → Transferência Bancária
```

### Receitas (Type: Income)
```
Descrição                                → Categoria                   → Subcategoria
=======================================================================================
Rendimentos                             → Renda de Investimento       → Rendimento de Juros
Salario EMPRESA XPTO                    → Finanças & Investimento     → Ganhos Ocupacionais
Transacao cancelada AMAZON              → Receitas                    → Estornos
```

### Despesas (Type: Expense)
```
Descrição                                → Categoria          → Subcategoria
===============================================================================
Pagamento com QR Pix AMAZON             → Compras            → Compras Online
Pagamento com QR Pix SHPP BRASIL        → Compras            → Compras Varejo
Boleto de luz COPEL                     → Despesas Fixas     → Boletos
iFood Restaurante XYZ                   → Alimentação        → Restaurantes
```

---

## Estrutura de Pastas

```
ofx-converter/
├── entrada/              # Coloque arquivos .ofx ou .csv aqui
│   └── lido/            # Arquivos processados (organizados por mês)
│       ├── 10-2025/
│       └── 11-2025/
├── convertido/          # Arquivos .csv + .qif prontos (organizados por mês)
│   ├── 10-2025/
│   │   ├── arquivo.csv  (ezBookkeeping)
│   │   └── arquivo.qif  (compatibilidade)
│   └── 11-2025/
└── logs/               # Logs da aplicação
```

---

## Troubleshooting

### Arquivos não são processados

**Verifique:**
- Extensão é `.ofx`, `.qfx` ou `.csv`?
- CSV é do Mercado Pago? (header `INITIAL_BALANCE;CREDITS;...`)
- Logs: `docker-compose logs -f`

### Transferências categorizadas incorretamente

**"Pagamento com QR Pix" sendo Transfer:**
- Problema: YAML tem palavra genérica (ex: `pix`)
- Solução: Use frases completas: `transacao pix enviada`

**Transferências sendo Expense:**
- Problema: Falta no YAML transferencias
- Solução: Adicione frase completa em `transferencias:`

### Categorias não aplicadas

```bash
# Rebuild do zero:
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Veja logs:
docker-compose logs -f | grep "categorize_smart"
```

### CSV não importa no ezBookkeeping

**Verifique:**
- Encoding UTF-8?
- Formato correto? (primeira linha = header)
- Account/Account2 preenchidos durante importação?

---

## Desenvolvimento

### Executar Localmente (sem Docker)

```bash
# Instalar dependências
pip install ofxparse pyyaml

# Executar
python ofx_converter.py
```

### Testar Categorização

```bash
python test_categorizer.py
```

```python
# test_categorizer.py
import sys
sys.path.insert(0, '.')
from services.categorizer import TransactionCategorizer

c = TransactionCategorizer('categorias.yaml')

desc = "Transacao Pix recebida Rodrigo"
result = c.categorize_smart(desc, 1000.0)
print(f"Type: {result['type']}")
print(f"Category: {result['category']}")
print(f"Subcategory: {result['subcategory']}")
```

---

## CSV ezBookkeeping - Campos

| Campo | Descrição | Exemplo |
|-------|-----------|---------|
| Time | Data/hora | `2025-11-03 00:00:00` |
| Timezone | Fuso horário | `-03:00` |
| Type | Transfer/Income/Expense | `Transfer` |
| Category | Categoria principal | `Transferência Geral` |
| Sub Category | Subcategoria | `Transferência Bancária` |
| Account | Conta origem (vazio) | `` |
| Account Currency | Moeda | `BRL` |
| Amount | Valor | `1000.00` |
| Account2 | Conta destino (vazio) | `` |
| Account2 Currency | Moeda | `BRL` |
| Account2 Amount | Valor | `1000.00` |
| Geographic Location | Localização (vazio) | `` |
| Tags | Tags (vazio) | `` |
| Description | Descrição original | `Transacao Pix recebida...` |

**Nota:** Account e Account2 ficam vazios para você preencher durante a importação no ezBookkeeping.

---

## Histórico de Versões

### v4.0 (Atual)
- Suporte a Mercado Pago CSV
- Geração CSV ezBookkeeping (além de QIF)
- Subcategorias em receitas/despesas
- Detecção inteligente de transferências via YAML
- Account/Account2 configuráveis na importação
- Categorização 100% via YAML (sem hardcode)

### v3.0
- Arquitetura modular com services
- Categorização via YAML

### v2.0
- Organização por mês-ano
- Correção de datas

### v1.0
- Versão inicial OFX → QIF

---

## Documentação Adicional

- `categorization_guide.md` - Guia completo de categorização
- `test_summary.md` - Testes e validação
- `walkthrough.md` - Passo a passo da implementação

---

## Contribuindo

Problemas ou sugestões? Abra uma issue!

---

## Licença

MIT


```
ofx-converter/
├── ofx_converter.py              # Orquestrador principal
├── services/                     # Serviços modulares
│   ├── mercadopago_parser.py    # Parser Mercado Pago CSV
│   ├── ofx_parser.py             # Parser OFX
│   ├── categorizer.py            # Categorização via YAML
│   ├── ezbookkeeping_csv_writer.py  # Gerador CSV ezBookkeeping
│   ├── qif_writer.py             # Gerador QIF
│   ├── file_reader.py            # Leitura multi-encoding
│   ├── date_extractor.py         # Extração de datas
│   └── text_normalizer.py       # Normalização UTF-8
├── categorias.yaml               # ⚙️ Regras de categorização (EDITÁVEL!)
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## 🚀 Como Usar

### 1. Configuração Inicial

```bash
chmod +x setup.sh
./setup.sh
```

### 2. Iniciar o Conversor

```bash
docker-compose up -d
```

### 3. Converter Arquivos

#### Mercado Pago CSV
```bash
# Copiar arquivo para entrada/
cp account_statement_xxxxx.csv entrada/mercadopago-11-2025.csv

# Aguardar conversão automática (5 segundos)
# Arquivos gerados em convertido/MM-YYYY/:
#   - mercadopago-11-2025.csv  (ezBookkeeping)
#   - mercadopago-11-2025.qif  (compatibilidade)
```

#### OFX/QFX (Bancos)
```bash
# Copiar arquivo para entrada/
cp extrato_nubank.ofx entrada/

# Arquivos gerados em convertido/MM-YYYY/:
#   - extrato_nubank.csv  (ezBookkeeping)
#   - extrato_nubank.qif  (compatibilidade)
```

### 4. Importar no ezBookkeeping

1. Abra ezBookkeeping
2. Vá em **Importar Dados**
3. Selecione o arquivo `.csv` gerado
4. **Preencha Account/Account2** para transferências durante importação
5. Pronto! Categorias e subcategorias já estarão aplicadas

### 5. Ver Logs

```bash
docker-compose logs -f
```

### 6. Parar o Conversor

```bash
docker-compose down
```

---

## Configuração de Categorias

### Estrutura do `categorias.yaml`

```yaml
# Receitas com subcategorias
receitas:
  - categoria: Renda de Investimento
    subcategoria: Rendimento de Juros
    palavras:
      - rendimento
      - rendimentos
      - dividendo

# Despesas com subcategorias
despesas:
  - categoria: Compras
    subcategoria: Compras Online
    palavras:
      - pagamento com qr pix amazon
      - marketplace

# Transferências (frases completas!)
transferencias:
  - categoria: Transferência Geral
    subcategoria: Transferência Bancária
    palavras:
      - transacao pix enviada
      - transacao pix recebida
      - transferencia pix enviada
```

### Como Adicionar Novas Transferências

**Use frases completas para evitar falsos positivos:**

```yaml
transferencias:
  - categoria: Transferência Geral
    subcategoria: Transferência Bancária
    palavras:
      # Adicione aqui pessoas específicas que você transfere:
      - transacao pix enviada maria silva
      - transacao pix recebida joao santos
      - transferencia nubank recebida pedro
```

### Como Adicionar Novas Categorias

```yaml
despesas:
  - categoria: Saúde
    subcategoria: Academia
    palavras:
      - smart fit
      - bodytech
      - mensalidade academia
```

### Aplicar Mudanças

```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

---

## Exemplos de Categorização

### Transferências (Type: Transfer)
```
Descrição                                → Categoria              → Subcategoria
===============================================================================
Transacao Pix recebida Rodrigo          → Transferência Geral    → Transferência Bancária
Transacao Pix enviada Carine            → Transferência Geral    → Transferência Bancária
```

### Receitas (Type: Income)
```
Descrição                                → Categoria                   → Subcategoria
=======================================================================================
Rendimentos                             → Renda de Investimento       → Rendimento de Juros
Salario EMPRESA XPTO                    → Finanças & Investimento     → Ganhos Ocupacionais
Transacao cancelada AMAZON              → Receitas                    → Estornos
```

### Despesas (Type: Expense)
```
Descrição                                → Categoria          → Subcategoria
===============================================================================
Pagamento com QR Pix AMAZON             → Compras            → Compras Online
Pagamento com QR Pix SHPP BRASIL        → Compras            → Compras Varejo
Boleto de luz COPEL                     → Despesas Fixas     → Boletos
iFood Restaurante XYZ                   → Alimentação        → Restaurantes
```

---

## Estrutura de Pastas

```
ofx-converter/
├── entrada/              ← Coloque arquivos .ofx ou .csv aqui
│   └── lido/            ← Arquivos processados (organizados por mês)
│       ├── 10-2025/
│       └── 11-2025/
├── convertido/          ← Arquivos .csv + .qif prontos (organizados por mês)
│   ├── 10-2025/
│   │   ├── arquivo.csv  (ezBookkeeping)
│   │   └── arquivo.qif  (compatibilidade)
│   └── 11-2025/
└── logs/               ← Logs da aplicação
```

---

## Troubleshooting

### Arquivos não são processados

**Verifique:**
- Extensão é `.ofx`, `.qfx` ou `.csv`?
- CSV é do Mercado Pago? (header `INITIAL_BALANCE;CREDITS;...`)
- Logs: `docker-compose logs -f`

### Transferências categorizadas incorretamente

**"Pagamento com QR Pix" sendo Transfer:**
- Problema: YAML tem palavra genérica (ex: `pix`)
- Solução: Use frases completas: `transacao pix enviada`

**Transferências sendo Expense:**
- Problema: Falta no YAML transferencias
- Solução: Adicione frase completa em `transferencias:`

### Categorias não aplicadas

```bash
# Rebuild do zero:
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Veja logs:
docker-compose logs -f | grep "categorize_smart"
```

### CSV não importa no ezBookkeeping

**Verifique:**
- Encoding UTF-8?
- Formato correto? (primeira linha = header)
- Account/Account2 preenchidos durante importação?

---

## Desenvolvimento

### Executar Localmente (sem Docker)

```bash
# Instalar dependências
pip install ofxparse pyyaml

# Executar
python ofx_converter.py
```

### Testar Categorização

```bash
python test_categorizer.py
```

```python
# test_categorizer.py
import sys
sys.path.insert(0, '.')
from services.categorizer import TransactionCategorizer

c = TransactionCategorizer('categorias.yaml')

desc = "Transacao Pix recebida Rodrigo"
result = c.categorize_smart(desc, 1000.0)
print(f"Type: {result['type']}")
print(f"Category: {result['category']}")
print(f"Subcategory: {result['subcategory']}")
```

---

## CSV ezBookkeeping - Campos

| Campo | Descrição | Exemplo |
|-------|-----------|---------|
| Time | Data/hora | `2025-11-03 00:00:00` |
| Timezone | Fuso horário | `-03:00` |
| Type | Transfer/Income/Expense | `Transfer` |
| Category | Categoria principal | `Transferência Geral` |
| Sub Category | Subcategoria | `Transferência Bancária` |
| Account | Conta origem (vazio) | `` |
| Account Currency | Moeda | `BRL` |
| Amount | Valor | `1000.00` |
| Account2 | Conta destino (vazio) | `` |
| Account2 Currency | Moeda | `BRL` |
| Account2 Amount | Valor | `1000.00` |
| Geographic Location | Localização (vazio) | `` |
| Tags | Tags (vazio) | `` |
| Description | Descrição original | `Transacao Pix recebida...` |

> **Nota:** Account e Account2 ficam **vazios** para você preencher durante a importação no ezBookkeeping.

---

## Histórico de Versões

### v5.0 (Atual)
- Suporte completo a XP Cartão de Crédito CSV
- Categorização 100% alinhada com ezBookkeeping
- Todas categorias e subcategorias do ezBookkeeping implementadas
- BOM handling automático (UTF-8 with signature)
- Formatação inteligente de parcelas em descrições
- Correção de keywords genéricas causando falsos positivos

### v4.0
- Suporte a Mercado Pago CSV
- Geração CSV ezBookkeeping (além de QIF)
- Subcategorias em receitas/despesas
- Detecção inteligente de transferências via YAML
- Account/Account2 configuráveis na importação
- Categorização 100% via YAML (sem hardcode)

### v3.0
- Arquitetura modular com services
- Categorização via YAML

### v2.0
- Organização por mês-ano
- Correção de datas

### v1.0
- Versão inicial OFX → QIF

---

## Documentação Adicional

- `categorization_guide.md` - Guia completo de categorização
- `test_summary.md` - Testes e validação
- `walkthrough.md` - Passo a passo da implementação

---

## Contribuindo

Problemas ou sugestões? Abra uma issue!

---

## Licença

MIT
