# Phase 1: Validacao com Dados Reais

## Objetivo

Rodar o conversor contra os 9 samples de maio/2026, corrigir todos os bugs encontrados, e garantir que o output CSV esteja no formato correto do EZBookkeeping com categorizacao e account matching funcionando.

Meta: todos os 9 samples processam com sucesso, gerando CSV valido e com conta correta atribuida.

---

## Wave 1: Test Harness + Baseline de Erros

### Task 1.1: Criar script de validacao batch

**Descricao:** Criar um script Python que processa todos os 9 samples da phase 1, captura erros/warnings, e gera um relatorio estruturado com status de cada arquivo.

**Arquivos envolvidos:**
- `tests/run_samples.py` (criar)
- `tests/__init__.py` (criar)

**Acoes:**
1. Criar `tests/run_samples.py` que:
   - Importa o pipeline e registry do projeto
   - Itera sobre os 9 samples em `samples/`
   - Para cada arquivo: tenta processar via registry + pipeline
   - Captura e registra: erro de parse, erro de account matching, erro de escrita CSV
   - Gera output em formato tabela no terminal: `[OK/FAIL] filename — mensagem`
   - Salva resultado detalhado em `tests/results/baseline_report.txt`
   - NAO move arquivos (modo dry-run) — escreve CSV em `tests/results/`
2. O script deve funcionar standalone (sem Docker): `python tests/run_samples.py`
3. Excluir os 2 PDFs do Mercado Pago (sao Phase 2)

**Samples a processar (9 arquivos):**
```
Extrato_banco_do_brasil_052026.ofx
inter_rodrigo_Extrato-01-05-2026-a-31-05-2026-OFX.ofx
xp_rodrigo_digital_extrato_de_01-05-2026_ate_31-05-2026.ofx
Fatura_xp_2026-06-15.csv
rico_carine_digital_extrato_de_01-05-2026_ate_31-05-2026.ofx
carine_rico_extrato_investimento_de_01-05-2026_ate_31-05-2026.xlsx
rodrigo_nubank_digital_extrato_60330829_01MAI2026_31MAI2026.ofx
Nubank_fatura_rodrigo_2026-06-15.ofx
rodrigo_xp_investimentoextrato_de_01-05-2026_ate_31-05-2026.xlsx
```

**Criterio de aceite:**
- Script executa sem crash
- Gera relatorio mostrando status de cada sample
- Identifica quais samples falham e em qual etapa (parse, account match, CSV write)

---

## Wave 2: Correcao de Bugs (parallelizavel)

### Task 2.1: Corrigir account matching do Banco do Brasil

**Descricao:** O arquivo `Extrato_banco_do_brasil_052026.ofx` normaliza para `extrato banco do brasil 052026`. A keyword `bancodobrasil` em contas.yaml nao faz match com `banco do brasil` (com espacos). Alem disso, nao tem `rodrigo` no nome, entao titular_match falha tambem. Resultado: score < 2, nenhuma conta encontrada.

**Arquivos envolvidos:**
- `contas.yaml`

**Acoes:**
1. Adicionar keyword `banco do brasil` (com espacos) na lista `banco` da conta "Banco do Brasil Rodrigo"
2. Resultado esperado: `banco: [bb, bancodobrasil, banco do brasil]`
3. Isso garante banco_match=true. Combinado com tipo_match (keyword `extrato` presente), score=2, suficiente para match.

**Criterio de aceite:**
- `AccountMatcher.match_account("Extrato_banco_do_brasil_052026.ofx")` retorna `"Banco do Brasil Rodrigo"`

---

### Task 2.2: Verificar e corrigir matching do Nubank fatura

**Descricao:** O arquivo `Nubank_fatura_rodrigo_2026-06-15.ofx` normaliza para `nubank fatura rodrigo 2026 06 15`. Precisa verificar se o OFXProcessor o pega (extensao .ofx) e se o account matcher resolve para `CC NuBank Rodrigo` (banco: nubank, titular: rodrigo, tipo: fatura — score 3).

**Arquivos envolvidos:**
- Verificacao apenas (nenhuma alteracao esperada, mas corrigir se necessario)
- `services/processors/ofx_processor.py`
- `contas.yaml`

**Acoes:**
1. Validar que OFXProcessor.can_handle() aceita este arquivo (.ofx = sim)
2. Validar que account matcher retorna `CC NuBank Rodrigo`
3. Se o OFX parser falhar no parse (fatura de cartao tem formato diferente de extrato), investigar e corrigir o `ofx_parser.py`

**Criterio de aceite:**
- Arquivo processa sem erro
- Conta atribuida: `CC NuBank Rodrigo`

---

### Task 2.3: Verificar deteccao do XP Investimento XLSX

**Descricao:** O arquivo `rodrigo_xp_investimentoextrato_de_01-05-2026_ate_31-05-2026.xlsx` precisa ser detectado pelo `RicoInvestimentoProcessor`. O can_handle verifica: extensao .xlsx + "investimento" no filename + ("rico" ou "xp"). Filename contem "investimento" (em "investimentoextrato") e "xp". Deve funcionar, mas validar.

**Arquivos envolvidos:**
- `services/processors/rico_investimento_processor.py`
- `services/rico_investimento_parser.py`

**Acoes:**
1. Confirmar que `can_handle()` retorna True para este filename
2. Confirmar que o parser consegue ler o XLSX sem erro
3. Se `investimentoextrato` (junto) nao matchear `'investimento' in filename_lower`, corrigir — na verdade "investimento" IS contained em "investimentoextrato", entao deve funcionar
4. Corrigir qualquer bug de parsing do XLSX

**Criterio de aceite:**
- Arquivo detectado pelo processor correto
- Parse retorna lista de transacoes nao-vazia
- Conta atribuida: `Conta Investimento XP Rodrigo`

---

### Task 2.4: Verificar e corrigir Fatura XP CSV

**Descricao:** O arquivo `Fatura_xp_2026-06-15.csv` precisa ser detectado pelo `XPCProcessor` (cartao de credito). O processor verifica header `Data;Estabelecimento;Portador;Valor;Parcela`. Precisa confirmar que o CSV real tem esse header. Account matching: normaliza para `fatura xp 2026 06 15` — banco: xp (match), tipo: fatura (match), titular: nenhum match. Score=2, suficiente. Mas sem titular, pode matchear errado se houver outra conta XP fatura.

**Arquivos envolvidos:**
- `services/processors/xp_cc_processor.py`
- `services/xp_cc_parser.py`
- `contas.yaml` (se precisar ajuste)

**Acoes:**
1. Verificar header do CSV real em `samples/Fatura_xp_2026-06-15.csv`
2. Se header divergir do esperado pelo processor, ajustar o processor
3. Verificar account matching — score 2 (banco+tipo) sem titular. Como nao tem "carine" no nome, e o "CC XP Rodrigo" requer titular rodrigo (que nao esta no filename!), o match vai FALHAR (score 1 apenas: banco=xp). Corrigir adicionando keyword na contas.yaml ou ajustando o arquivo
4. Solucao provavel: adicionar `fatura` como keyword em `tipo` de "CC XP Rodrigo" (ja esta la). O problema real eh que titular nao matcha. Precisa decidir: adicionar keyword sem titular requirement, ou adicionar logic que trata fatura sem titular como do rodrigo (owner default).

**NOTA:** Re-analisando o matching: banco=[xp] match, tipo=[cc, fatura, cartao] match com "fatura", titular=[rodrigo] NAO match (nao tem rodrigo no nome). Score = 2 (banco + tipo). Threshold eh >= 2. Portanto DEVE funcionar. Validar no teste.

**Criterio de aceite:**
- CSV parseado corretamente pelo XPCProcessor
- Conta atribuida: `CC XP Rodrigo`
- Transacoes extraidas com campos corretos

---

### Task 2.5: Corrigir bugs adicionais encontrados no baseline

**Descricao:** Apos rodar o test harness (Task 1.1), qualquer bug adicional nao previsto nas tasks acima deve ser corrigido aqui. Esta task eh um catch-all para problemas descobertos no baseline.

**Arquivos envolvidos:**
- Dependente dos erros encontrados
- Provavelmente: parsers em `services/`, `contas.yaml`

**Acoes:**
1. Analisar o relatorio do baseline (`tests/results/baseline_report.txt`)
2. Para cada sample que falhou e nao esta coberto pelas tasks 2.1-2.4, diagnosticar e corrigir
3. Bugs provaveis (da pesquisa):
   - Amount retornado como str em vez de float em algum parser
   - Transfer sem Account2 preenchido no writer
   - XP CC sign inversion assimetrica
   - Trailing spaces em contas.yaml (trim nas keywords)
4. Corrigir cada bug e re-rodar o test harness

**Criterio de aceite:**
- Todos os 9 samples passam no test harness (status OK)
- Nenhum erro de parse, account match, ou CSV write

---

## Wave 3: Validacao de Output

### Task 3.1: Validar formato CSV do EZBookkeeping

**Descricao:** Verificar que todos os CSVs gerados seguem o formato exato esperado pelo EZBookkeeping.

**Arquivos envolvidos:**
- `tests/validate_csv_format.py` (criar)
- CSVs gerados em `tests/results/`

**Acoes:**
1. Criar script `tests/validate_csv_format.py` que:
   - Le cada CSV gerado
   - Valida header exato: `Time,Timezone,Type,Category,Sub Category,Account Currency,Amount,Account2,Account2 Currency,Account2 Amount,Geographic Location,Tags,Description`
   - Valida que Timezone eh sempre `-03:00`
   - Valida que Currency eh sempre `BRL`
   - Valida que Amount eh numerico com 2 decimais (sem sinal negativo — deve ser abs)
   - Valida que Type eh um de: `Expense`, `Income`, `Transfer`
   - Valida que Account (na coluna correspondente — verificar se ta no header ou eh implicito) esta preenchido
   - Valida que nao ha linhas vazias ou malformadas
2. Comparar com o sample de referencia: `samples/ezBookkeeping_Rodrigo_dados_exportados.csv`
3. Reportar diferencas de formato

**Criterio de aceite:**
- Todos os 9 CSVs gerados passam na validacao de formato
- Nenhum campo obrigatorio vazio (exceto Account2 para non-transfer, Geographic Location, Tags)

---

### Task 3.2: Validar categorizacao e account matching

**Descricao:** Verificar que as transacoes estao sendo categorizadas (nao ficam com categoria vazia) e que a conta atribuida esta correta para cada sample.

**Arquivos envolvidos:**
- `tests/validate_categorization.py` (criar)
- `categorias.yaml`
- `contas.yaml`

**Acoes:**
1. Criar script `tests/validate_categorization.py` que:
   - Le cada CSV gerado
   - Reporta % de transacoes com categoria vazia (meta: < 30% sem categoria eh aceitavel — keywords nao cobrem tudo)
   - Reporta a conta usada em cada CSV
   - Valida que cada sample esta vinculado a conta esperada:
     ```
     Extrato_banco_do_brasil_052026.ofx → Banco do Brasil Rodrigo
     inter_rodrigo_Extrato-*.ofx → Conta Inter Rodrigo
     xp_rodrigo_digital_extrato_*.ofx → Conta Digital XP Rodrigo
     Fatura_xp_2026-06-15.csv → CC XP Rodrigo
     rico_carine_digital_extrato_*.ofx → Conta Digital Rico Carine
     carine_rico_extrato_investimento_*.xlsx → Conta Investimento Rico Carine
     rodrigo_nubank_digital_extrato_*.ofx → NuConta Rodrigo
     Nubank_fatura_rodrigo_*.ofx → CC NuBank Rodrigo
     rodrigo_xp_investimentoextrato_*.xlsx → Conta Investimento XP Rodrigo
     ```
2. Se alguma conta estiver errada, documentar no relatorio

**Criterio de aceite:**
- Todas as 9 contas estao corretas conforme tabela acima
- Categorizacao funciona (pelo menos 70% das transacoes tem categoria atribuida, ou justificativa para menos)

---

## Wave 4: Teste de Integracao End-to-End

### Task 4.1: Rodar todos os samples end-to-end e gerar relatorio final

**Descricao:** Executar o conversor completo (via script, nao Docker) contra todos os 9 samples e confirmar que o fluxo inteiro funciona: deteccao → parse → postprocess → CSV → resultado correto.

**Arquivos envolvidos:**
- `tests/run_samples.py` (ja criado, re-executar)
- `tests/validate_csv_format.py` (re-executar)
- `tests/validate_categorization.py` (re-executar)

**Acoes:**
1. Limpar `tests/results/`
2. Rodar `python tests/run_samples.py`
3. Rodar `python tests/validate_csv_format.py`
4. Rodar `python tests/validate_categorization.py`
5. Confirmar: 9/9 samples OK, 9/9 CSVs validos, 9/9 contas corretas
6. Documentar resultado final

**Criterio de aceite:**
- 9/9 samples processados com sucesso
- 9/9 CSVs no formato correto do EZBookkeeping
- 9/9 contas atribuidas corretamente
- Zero erros de parse

---

## Resumo de Dependencias

```
Wave 1: [Task 1.1] — sem dependencias
Wave 2: [Task 2.1, 2.2, 2.3, 2.4] — dependem de Wave 1 (precisam do test harness)
         [Task 2.5] — depende de Wave 1 + resultado do baseline
Wave 3: [Task 3.1, 3.2] — dependem de Wave 2 (precisam dos bugs corrigidos)
Wave 4: [Task 4.1] — depende de Wave 3 (validacao final)
```

## Criterio de Sucesso da Phase 1

- [ ] Todos os 9 samples processam sem erro
- [ ] Todos os 9 CSVs gerados estao no formato EZBookkeeping correto
- [ ] Account matching retorna a conta certa para cada sample
- [ ] Categorizacao esta funcionando (categorias atribuidas onde ha keyword match)
- [ ] Scripts de teste existem e podem ser re-executados a qualquer momento
