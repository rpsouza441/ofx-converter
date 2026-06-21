# Arquitetura do conversor OFX

## Fluxo de conversão

```mermaid
flowchart TD
    A[OFXConverter monitora entrada] --> B[Arquivo encontrado]
    B --> C[ProcessorRegistry procura processor]
    C --> D{FileProcessor compatível?}
    D -->|não| E[Arquivo ignorado]
    D -->|sim| F[Processor concreto parseia arquivo]
    F --> G[ConversionPipeline recebe transações]
    G --> H[AccountMatcher identifica conta]
    H --> I[TransactionPostProcessor aplica ajustes]
    I --> J[EZBookkeepingCSVWriter escreve CSV]
    J --> K[Arquivo original movido para entrada/lido]
```

## Sequência de chamadas

```mermaid
sequenceDiagram
    participant Converter as OFXConverter
    participant Registry as ProcessorRegistry
    participant Processor as FileProcessor
    participant Pipeline as ConversionPipeline
    participant Matcher as AccountMatcher
    participant Post as TransactionPostProcessor
    participant Writer as EZBookkeepingCSVWriter

    Converter->>Converter: monitora pasta entrada
    Converter->>Registry: find(file_path)
    Registry->>Processor: can_handle(file_path)
    Processor-->>Registry: true
    Registry-->>Converter: processor
    Converter->>Pipeline: convert(file_path, processor)
    Pipeline->>Processor: parse(file_path)
    Processor-->>Pipeline: transactions
    Pipeline->>Matcher: match_account(file_name)
    Matcher-->>Pipeline: account_name
    Pipeline->>Post: process(transactions, account_name)
    Post-->>Pipeline: transactions
    Pipeline->>Writer: create_csv_file(csv_path)
    Pipeline->>Writer: write_transfer/write_expense/write_income
    Pipeline->>Writer: close()
    Pipeline->>Pipeline: move original para entrada/lido
    Pipeline-->>Converter: resultado
```

## Relação entre componentes

```mermaid
classDiagram
    class OFXConverter {
        +scan_and_convert()
        +watch()
    }

    class ProcessorRegistry {
        +find(file_path)
        +get(key)
    }

    class FileProcessor {
        <<interface>>
        +can_handle(file_path)
        +parse(file_path)
    }

    class OFXProcessor
    class MercadoPagoProcessor
    class RicoProcessor
    class XPCCProcessor
    class XPContaProcessor
    class BBProcessor

    class ConversionPipeline {
        +convert(file_path, processor)
    }

    class TransactionPostProcessor {
        +process(transactions, account_name)
    }

    class AccountMatcher {
        +match_account(file_name)
    }

    class EZBookkeepingCSVWriter {
        +create_csv_file(csv_path)
        +write_transfer()
        +write_expense()
        +write_income()
        +close()
    }

    OFXConverter --> ProcessorRegistry
    OFXConverter --> ConversionPipeline
    ProcessorRegistry --> FileProcessor

    FileProcessor <|.. OFXProcessor
    FileProcessor <|.. MercadoPagoProcessor
    FileProcessor <|.. RicoProcessor
    FileProcessor <|.. XPCCProcessor
    FileProcessor <|.. XPContaProcessor
    FileProcessor <|.. BBProcessor

    ConversionPipeline --> FileProcessor
    ConversionPipeline --> AccountMatcher
    ConversionPipeline --> TransactionPostProcessor
    ConversionPipeline --> EZBookkeepingCSVWriter
```

## Observação

Parsers internos existem, mas ficaram fora dos diagramas porque não estavam na lista de componentes solicitada.
