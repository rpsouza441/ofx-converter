# Roadmap — ofx-converter

## Phase 1: Validacao com Dados Reais (maio/2026)
**Status:** not started
**Objetivo:** Rodar o conversor contra os samples de maio/2026 e corrigir bugs.

### Samples disponiveis
- Extrato_banco_do_brasil_052026.ofx
- inter_rodrigo_Extrato-01-05-2026-a-31-05-2026-OFX.ofx
- xp_rodrigo_digital_extrato_de_01-05-2026_ate_31-05-2026.ofx
- Fatura_xp_2026-06-15.csv
- rico_carine_digital_extrato_de_01-05-2026_ate_31-05-2026.ofx
- carine_rico_extrato_investimento_de_01-05-2026_ate_31-05-2026.xlsx
- rodrigo_nubank_digital_extrato_60330829_01MAI2026_31MAI2026.ofx
- Nubank_fatura_rodrigo_2026-06-15.ofx
- rodrigo_xp_investimentoextrato_de_01-05-2026_ate_31-05-2026.xlsx
- mp_rodrigo_extrato_pdf_260621110308.pdf (Phase 2)
- mp_extrato_carine_260621111649.pdf (Phase 2)

### Tarefas
1. Rodar conversor contra cada sample OFX/CSV/XLSX e registrar erros
2. Corrigir bugs encontrados nos parsers
3. Validar output CSV no formato correto do EZBookkeeping
4. Garantir categorizacao e account matching funcionam

---

## Phase 2: Parser PDF do Mercado Pago
**Status:** not started
**Objetivo:** Implementar parser para PDF do Mercado Pago (nao exporta mais CSV).

### Tarefas
1. Analisar estrutura do PDF
2. Implementar extracao (pdfplumber ou similar)
3. Criar MercadoPagoPDFProcessor
4. Integrar com pipeline e registry
5. Testar com samples reais

---

## Phase 3: Automacao e UX
**Status:** not started
**Objetivo:** Minimizar intervencao manual no uso mensal.

### Tarefas
1. Melhorar deteccao automatica de novos formatos nos samples
2. Explorar integracao MCP para importacao direta no EZBookkeeping
3. Melhorar logging e feedback ao usuario

---

## Phase 4: Polish
**Status:** not started
**Objetivo:** Robustez e manutenibilidade.

### Tarefas
1. Testes automatizados (pytest)
2. Error handling robusto
3. Documentacao atualizada
4. CI com testes
