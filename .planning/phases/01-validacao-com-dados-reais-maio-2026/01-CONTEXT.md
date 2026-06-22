# Phase 1: Validacao com Dados Reais (maio/2026) - Context

**Gathered:** 2026-06-22
**Status:** Ready for planning

<domain>
## Phase Boundary

Rodar o conversor contra todos os samples de maio/2026 (OFX/CSV/XLSX), identificar e corrigir bugs nos parsers, e validar que o output CSV importa corretamente no EZBookkeeping. Samples de PDF do Mercado Pago sao Phase 2.

</domain>

<decisions>
## Implementation Decisions

### Criterio de Validacao
- **D-01:** A validacao final e importar o CSV gerado no EZBookkeeping e confirmar que as transacoes aparecem com valores, datas, categorias e contas corretas.
- **D-02:** Usar `samples/ezBookkeeping_Rodrigo_dados_exportados.csv` como referencia de formato — o output gerado deve seguir exatamente o mesmo schema (14 colunas, mesmos nomes de conta, mesma formatacao de valores e datas).

### Tratamento de Formatos
- **D-03:** Analisar previamente cada sample file antes de rodar — entender a estrutura do arquivo para saber quais parsers vao precisar de ajuste (em vez de simplesmente rodar e esperar falhar).
- **D-04:** Formatos a validar: BB como OFX (nao CSV), Nubank fatura de cartao (OFX), XP investimento XLSX (reutiliza RicoInvestimentoProcessor que ja detecta 'xp'), Rico conta digital OFX, Rico investimento XLSX, Inter OFX, XP conta digital OFX, XP cartao credito CSV.

### Comportamento em Caso de Erro
- **D-05:** Se um arquivo falhar no parse, logar o erro e continuar para o proximo. O arquivo com erro fica em `entrada/` para reprocessar depois (nao mover para pasta de erro, nao parar o processamento).

### Claude's Discretion
- Ordem de validacao dos samples (qual rodar primeiro)
- Nivel de detalhe dos logs de erro
- Estrategia de fix (corrigir parser existente vs criar parser dedicado)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Formato de Output
- `samples/ezBookkeeping_Rodrigo_dados_exportados.csv` — CSV de referencia exportado do EZBookkeeping com formato exato esperado (nomes de conta, categorias, formato de data/valor)

### Configuracao
- `categorias.yaml` — Regras de categorizacao por keyword
- `contas.yaml` — Mapeamento arquivo -> conta no EZBookkeeping (nomes como "CC NuBank Rodrigo", "Conta Inter Rodrigo", etc.)

### Arquitetura
- `services/processor_registry.py` — Registry que resolve processor por arquivo
- `services/conversion_pipeline.py` — Pipeline: parse -> postprocess -> write CSV -> move input

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `ProcessorRegistry` com pattern `can_handle()` por file extension + keywords no nome
- `ConversionPipeline` unificado que centraliza todo o fluxo de conversao
- `EZBookkeepingCSVWriter` com metodos `write_expense/write_income/write_transfer`
- `AccountMatcher` baseado em keywords no nome do arquivo (titular + banco + tipo)
- `RicoInvestimentoProcessor` ja detecta tanto 'rico' quanto 'xp' no nome do XLSX

### Established Patterns
- Cada formato tem: Parser (extrai transacoes) + Processor (adapter com can_handle/parse)
- Transacoes retornam dicts com keys: date, amount, description, category, subcategory, type
- `type` pode ser: 'expense', 'income', 'transfer'
- Output CSV sempre em `convertido/MM-YYYY/`, input movido para `entrada/lido/MM-YYYY/`

### Integration Points
- `OFXProcessor` e generico para OFX (Nubank, Inter, XP conta) — usa `ofx_parser`
- `BBProcessor` espera CSV (usa `bb_parser.is_bb_csv()`) — BB como OFX vai cair no `OFXProcessor` generico
- `XPCCProcessor` detecta CSV de fatura XP por header

</code_context>

<specifics>
## Specific Ideas

- Nomes de conta no output devem bater com os do CSV de referencia: "CC NuBank Rodrigo", "CC NuBank Carine", "CC XP Rodrigo", "Conta Inter Rodrigo", "MercadoPago Carine", etc.
- Formato de data esperado: "YYYY-MM-DD HH:MM:SS"
- Valores com 2 casas decimais
- Timezone fixo: "-03:00"

</specifics>

<deferred>
## Deferred Ideas

- Parser PDF do Mercado Pago (Phase 2)
- Testes automatizados com pytest (Phase 4)

</deferred>

---

*Phase: 01-validacao-com-dados-reais-maio-2026*
*Context gathered: 2026-06-22*
