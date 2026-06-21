# UML arquitetura final

## Resumo

O projeto agora separa o fluxo comum de conversão da lógica específica de cada banco/formato.

`OFXConverter` inicializa dependências, monta processors, cria registry e executa o loop de monitoramento. `ProcessorRegistry` escolhe qual processor entende cada arquivo. `ConversionPipeline` executa o fluxo comum: parse, mês, conta, pós-processamento, escrita CSV e movimentação para `lido`.

## Responsabilidades

- `OFXConverter`: entrypoint, paths, dependências, loop `watch`, wrappers `convert_*`.
- `ProcessorRegistry`: resolve processor por prioridade de detecção.
- `FileProcessor`: contrato simples para `can_handle` e `parse`.
- Processors concretos: adaptam parsers atuais sem mudar regra interna.
- Parsers atuais: continuam lendo exports dos bancos/corretoras.
- `ConversionPipeline`: fluxo comum compartilhado por todos formatos.
- `TransactionPostProcessor`: ajustes após parse, hoje regra Nubank "Pagamento recebido".
- `AccountMatcher`: identifica conta ezBookkeeping pelo nome do arquivo.
- `DateExtractor`: extrai mês/ano para organizar saída.
- `EZBookkeepingCSVWriter`: escreve CSV final compatível com ezBookkeeping.

## Diagrama de classes

```mermaid
classDiagram
    class OFXConverter {
        +scan_and_convert()
        +watch()
        +convert_file(Path) bool
        +convert_mercadopago_file(Path) bool
        +convert_rico_file(Path) bool
        +convert_xp_cc_file(Path) bool
        +convert_xp_conta_file(Path) bool
        +convert_rico_investimento_file(Path) bool
        +convert_bb_file(Path) bool
    }

    class ConversionPipeline {
        +convert(Path, FileProcessor, bool) bool
        -_extract_month_year(Path, FileProcessor, list) str
        -_write_csv(Path, list, str)
        -_apply_ownership(Path)
    }

    class ProcessorRegistry {
        +find(Path) FileProcessor
        +get(str) FileProcessor
        +get_optional(str) FileProcessor
    }

    class FileProcessor {
        <<Protocol>>
        +key str
        +name str
        +can_handle(Path) bool
        +parse(Path) list
    }

    class OFXProcessor
    class MercadoPagoProcessor
    class RicoProcessor
    class RicoInvestimentoProcessor
    class XPCCProcessor
    class XPContaProcessor
    class BBProcessor

    class OFXParser
    class MercadoPagoParser
    class RicoParser
    class RicoInvestimentoParser
    class XPCCParser
    class XPContaParser
    class BBParser
    class TransactionPostProcessor {
        +process(list, str) list
    }
    class AccountMatcher {
        +match_account(str) str
    }
    class DateExtractor {
        +extract_month_year_from_transactions(list) str
        +extract_month_year_from_ofx(str) str
    }
    class EZBookkeepingCSVWriter {
        +create_csv_file(Path)
        +write_transfer(...)
        +write_expense(...)
        +write_income(...)
        +close()
    }

    OFXConverter --> ProcessorRegistry
    OFXConverter --> ConversionPipeline
    OFXConverter --> AccountMatcher
    OFXConverter --> DateExtractor
    OFXConverter --> TransactionPostProcessor

    ProcessorRegistry o-- FileProcessor
    FileProcessor <|.. OFXProcessor
    FileProcessor <|.. MercadoPagoProcessor
    FileProcessor <|.. RicoProcessor
    FileProcessor <|.. RicoInvestimentoProcessor
    FileProcessor <|.. XPCCProcessor
    FileProcessor <|.. XPContaProcessor
    FileProcessor <|.. BBProcessor

    OFXProcessor --> OFXParser
    MercadoPagoProcessor --> MercadoPagoParser
    RicoProcessor --> RicoParser
    RicoInvestimentoProcessor --> RicoInvestimentoParser
    XPCCProcessor --> XPCCParser
    XPContaProcessor --> XPContaParser
    BBProcessor --> BBParser

    ConversionPipeline --> DateExtractor
    ConversionPipeline --> AccountMatcher
    ConversionPipeline --> TransactionPostProcessor
    ConversionPipeline --> EZBookkeepingCSVWriter
```

## Diagrama de sequência

```mermaid
sequenceDiagram
    participant App as OFXConverter
    participant Registry as ProcessorRegistry
    participant Processor as FileProcessor
    participant Parser as Parser atual
    participant Pipeline as ConversionPipeline
    participant Post as TransactionPostProcessor
    participant Matcher as AccountMatcher
    participant Writer as EZBookkeepingCSVWriter
    participant FS as Sistema de arquivos

    App->>App: watch()
    App->>App: scan_and_convert()
    loop cada arquivo em entrada_dir
        App->>Registry: find(file_path)
        Registry->>Processor: can_handle(file_path)
        Processor-->>Registry: true/false
        Registry-->>App: processor selecionado
        App->>Pipeline: convert(file_path, processor, validate=False)
        Pipeline->>Processor: parse(file_path)
        Processor->>Parser: parse_csv/parse/parse_with_ofxparse
        Parser-->>Processor: transactions
        Processor-->>Pipeline: transactions
        Pipeline->>Pipeline: extrair month_year
        Pipeline->>Matcher: match_account(file_path.name)
        Matcher-->>Pipeline: account_name
        Pipeline->>Post: process(transactions, account_name)
        Post-->>Pipeline: transactions ajustadas
        Pipeline->>Writer: create_csv_file(csv_path)
        loop cada transação
            Pipeline->>Writer: write_transfer/write_expense/write_income
        end
        Pipeline->>Writer: close()
        Pipeline->>FS: move arquivo para entrada/lido/month_year
        Pipeline-->>App: True/False
    end
```

## Diagrama de fluxo

```mermaid
flowchart TD
    A[watch] --> B[scan_and_convert]
    B --> C{arquivo?}
    C -->|diretório| B
    C -->|arquivo| D[registry.find]
    D --> E{XP CC header?}
    E -->|sim| P1[XPCCProcessor]
    E -->|não| F{XP conta header?}
    F -->|sim| P2[XPContaProcessor]
    F -->|não| G{BB header?}
    G -->|sim| P3[BBProcessor]
    G -->|não| H{CSV com rico no nome?}
    H -->|sim| P4[RicoProcessor]
    H -->|não| I{Mercado Pago header?}
    I -->|sim| P5[MercadoPagoProcessor]
    I -->|não| J{.ofx ou .qfx?}
    J -->|sim| P6[OFXProcessor]
    J -->|não| K{XLSX investimento Rico/XP?}
    K -->|sim| P7[RicoInvestimentoProcessor]
    K -->|não| Z[ignorar/log debug]
    P1 --> L[pipeline.convert]
    P2 --> L
    P3 --> L
    P4 --> L
    P5 --> L
    P6 --> L
    P7 --> L
    L --> M[parse]
    M --> N[month_year]
    N --> O[match account]
    O --> Q[postprocess]
    Q --> R[write CSV ezBookkeeping]
    R --> S[move para lido/month_year]
```

## Métodos chamados em ordem

1. `OFXConverter.watch()`
2. `OFXConverter.scan_and_convert()`
3. `ProcessorRegistry.find(file_path)`
4. `processor.can_handle(file_path)`
5. `ConversionPipeline.convert(file_path, processor, validate=False)`
6. `processor.parse(file_path)`
7. Parser específico:
   - `OFXParser.parse_with_ofxparse()` e fallback `parse_with_regex()`
   - `MercadoPagoParser.parse_csv()`
   - `RicoParser.parse()`
   - `RicoInvestimentoParser.parse()`
   - `XPCCParser.parse_csv()`
   - `XPContaParser.parse_csv()`
   - `BBParser.parse()`
8. `DateExtractor.extract_month_year_from_transactions()` ou `extract_month_year_from_ofx()`
9. `AccountMatcher.match_account()`
10. `TransactionPostProcessor.process()`
11. `EZBookkeepingCSVWriter.create_csv_file()`
12. `EZBookkeepingCSVWriter.write_transfer/write_expense/write_income()`
13. `EZBookkeepingCSVWriter.close()`
14. `shutil.move()` para `entrada/lido/<month_year>/`
15. callback de ownership opcional.

## Como adicionar novo banco/formato

1. Criar ou adaptar parser em `services/`.
2. Criar processor em `services/processors/novo_banco_processor.py`.
3. Implementar `key`, `name`, `can_handle(file_path)` e `parse(file_path)`.
4. Exportar processor em `services/processors/__init__.py`.
5. Registrar processor em `OFXConverter._build_processors()` na ordem correta.
6. Adicionar teste/golden file quando existir massa segura.

O novo processor não deve escrever CSV, mover arquivo ou resolver conta. Essas etapas ficam no `ConversionPipeline`.
