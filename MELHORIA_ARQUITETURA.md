# Melhoria proposta: pipeline de conversão com adaptadores

## Contexto

O projeto converte exports de bancos/corretoras para CSV compatível com ezBookkeeping. Hoje já existem services separados para leitura, categorização, normalização, parsers e escrita CSV, mas a responsabilidade principal ainda está concentrada em `ofx_converter.py`.

`ofx_converter.py` tem 922 linhas e acumula:

- criação de diretórios;
- inicialização de todos os parsers;
- detecção de tipo de arquivo;
- escolha de parser;
- pós-processamento específico por conta;
- escrita no formato ezBookkeeping;
- movimentação do arquivo original para `entrada/lido`;
- aplicação de ownership;
- loop de monitoramento.

Isso funciona, mas dificulta atualização. Para adicionar ou ajustar banco, geralmente precisa mexer no orquestrador, no validador e no parser ao mesmo tempo.

## Ponto negativo principal

Responsabilidades estão parcialmente separadas, mas o fluxo de conversão ainda não está.

Os métodos `convert_mercadopago_file`, `convert_rico_file`, `convert_xp_cc_file`, `convert_xp_conta_file`, `convert_rico_investimento_file`, `convert_bb_file` e `convert_file` repetem quase o mesmo processo:

1. validar/detectar arquivo;
2. parsear transações;
3. extrair mês;
4. criar pasta de saída;
5. identificar conta;
6. escrever CSV;
7. mover arquivo para `lido`;
8. registrar logs.

Diferença real entre bancos fica pequena: como detectar arquivo e como parsear transações. O resto é pipeline comum.

## Melhoria recomendada

Criar camada de `processors` ou `adapters`, mantendo comportamento atual.

Cada banco/formato teria um adaptador com interface simples:

```python
class FileProcessor:
    name: str

    def can_handle(self, file_path: Path) -> bool:
        ...

    def parse(self, file_path: Path) -> list[dict]:
        ...
```

Exemplos:

- `OFXProcessor`
- `MercadoPagoProcessor`
- `RicoProcessor`
- `RicoInvestimentoProcessor`
- `XPCCProcessor`
- `XPContaProcessor`
- `BBProcessor`

O `OFXConverter` deixaria de conhecer detalhes de cada banco. Ele só faria:

```python
for file_path in entrada:
    processor = registry.find(file_path)
    if processor:
        pipeline.convert(file_path, processor)
```

## Nova divisão sugerida

```text
ofx_converter.py
  Mantém entrypoint, logging, watch loop.

services/conversion_pipeline.py
  Fluxo comum:
  parse -> postprocess -> resolve account -> write csv -> move input -> ownership.

services/processors/
  Um processor por banco/formato.
  Cada processor só detecta e parseia.

services/processor_registry.py
  Lista ordenada de processors.
  Resolve conflitos de detecção.

services/transaction_postprocessor.py
  Regras após parse, como "Pagamento recebido" em CC Nubank.

services/ezbookkeeping_csv_writer.py
  Continua como saída final.
```

## Por que melhora sem quebrar

Essa mudança pode ser incremental.

Primeiro passo não precisa alterar parsers existentes. Os processors podem só embrulhar classes atuais:

```python
class BBProcessor:
    name = "Banco do Brasil CSV"

    def __init__(self, bb_parser):
        self.bb_parser = bb_parser

    def can_handle(self, file_path):
        return BBParser.is_bb_csv(file_path)

    def parse(self, file_path):
        return self.bb_parser.parse(str(file_path))
```

Assim, comportamento interno de `BBParser`, `XPCCParser`, `MercadoPagoParser` etc. fica igual.

Depois, `OFXConverter` pode manter métodos antigos como wrappers:

```python
def convert_bb_file(self, csv_file: Path) -> bool:
    return self.pipeline.convert(csv_file, self.registry.get("bb"))
```

Isso preserva compatibilidade com qualquer chamada existente.

## Plano seguro

1. Adicionar testes/golden files antes da refatoração.

   Usar alguns exports reais já convertidos como referência. Rodar conversão em pasta temporária e comparar CSV gerado com CSV esperado.

2. Criar `ConversionPipeline`.

   Extrair somente fluxo repetido: criar pastas, escrever CSV, mover arquivo, ownership e logs.

3. Criar `FileProcessor` e registry.

   Processors chamam parsers atuais. Sem mudar regra de parse.

4. Trocar `scan_and_convert`.

   Em vez de várias listas por tipo, iterar arquivos uma vez e pedir ao registry o processor correto.

5. Manter métodos `convert_*`.

   Eles delegam para pipeline. Isso reduz risco e facilita rollback.

6. Mover pós-processamentos específicos.

   `_postprocess_transactions` vira lista de regras plugáveis. Exemplo: `NubankCreditCardPaymentRule`.

7. Só depois limpar duplicações antigas.

   Quando testes passarem e saída bater, remover código repetido.

## Ordem de detecção

Registry precisa ordem explícita porque alguns formatos usam `.csv` e podem conflitar.

Ordem sugerida:

1. XP cartão por header;
2. XP conta por header;
3. Banco do Brasil por header;
4. Rico por nome/header;
5. Mercado Pago por header;
6. OFX/QFX por extensão;
7. XLSX investimento por nome/extensão.

Melhor ainda: preferir detecção por header/conteúdo, não por nome, quando banco permitir.

## Benefício prático

Adicionar novo banco vira tarefa pequena:

1. criar parser ou adaptar parser existente;
2. criar processor com `can_handle` e `parse`;
3. registrar processor;
4. adicionar golden test.

Não precisa duplicar escrita CSV, movimentação de arquivo, criação de pasta nem logs.

## Riscos

- Detecção por nome ainda pode gerar falso positivo, especialmente Rico/XP investimento.
- Transações são `dict` livres; campos ausentes quebram só em runtime.
- Writer abre arquivo manualmente; erro no meio pode deixar arquivo aberto se não houver `finally` ou context manager.
- Alguns parsers também categorizam. Parser puro seria melhor, mas mudar isso agora aumenta risco.

## Próximo refinamento opcional

Depois da separação, criar modelo de transação:

```python
@dataclass
class Transaction:
    date: str
    amount: float
    description: str
    type: str
    category: str
    subcategory: str = ""
```

Isso reduz erros de chave (`txn['subcategory']`) e facilita validação antes de escrever CSV.

## Resumo

Melhoria mais segura: extrair pipeline comum e criar registry de processors.

Não muda formato de saída. Não muda parsers. Não muda uso via Docker. Só move responsabilidades para lugares menores, permitindo atualizar funções por banco com menos risco.
