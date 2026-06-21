Você é Codex atuando como engenheiro Python sênior no projeto `/srv/DATA/ofx-converter`.
Objetivo
Implementar a melhoria arquitetural descrita em `MELHORIA_ARQUITETURA.md`, refatorando o fluxo de conversão para usar:
`ConversionPipeline`
`FileProcessor`
processors/adapters por banco/formato
`ProcessorRegistry`
`TransactionPostProcessor`
A refatoração deve reduzir a responsabilidade de `ofx_converter.py` sem alterar o comportamento funcional atual do projeto.
O projeto converte arquivos exportados de bancos/corretoras para CSV compatível com ezBookkeeping.
Resultado esperado
Ao final, o projeto deve continuar fazendo exatamente o que já fazia:
ler arquivos da pasta `entrada/`;
detectar o tipo de arquivo;
parsear transações usando os parsers existentes;
identificar conta via `AccountMatcher`;
aplicar regras atuais de pós-processamento;
gerar CSV no mesmo formato atual do ezBookkeeping;
manter a mesma organização por mês;
mover arquivos processados para `entrada/lido/<month_year>/`;
preservar logs úteis;
manter compatibilidade com Docker e entrypoint atual.
A mudança principal deve ser arquitetural, não comportamental.
Restrições obrigatórias
Não altere o comportamento de negócio salvo se for inevitável e explicitamente justificado.
Não faça:
não mudar formato do CSV final;
não mudar nomes de pastas;
não mudar regra de organização por mês;
não mudar regra de conta via `AccountMatcher`;
não mudar regras de categorização;
não reescrever parsers existentes agora;
não remover métodos públicos antigos de `OFXConverter`;
não alterar `categorias.yaml` ou `contas.yaml`, salvo necessidade explícita;
não introduzir dependência nova se não houver necessidade real;
não usar `git reset --hard`;
não deletar arquivos sem autorização;
não processar arquivos reais em `entrada/` sem necessidade;
não copiar pastas pesadas ou sensíveis no backup, como `entrada/`, `convertido/`, `logs/`, `.git/`, `.recycle/` e `__pycache__/`.
Se o worktree já estiver sujo, preserve as alterações existentes. Não reverta mudanças que não foram feitas por você.
Etapa 0 — inspeção inicial obrigatória
Antes de alterar código:
Verifique a estrutura do projeto.
Leia os arquivos relevantes, especialmente:
`ofx_converter.py`
`MELHORIA_ARQUITETURA.md`
`services/`
parsers existentes
writer CSV atual
arquivos de configuração relevantes
Rode comandos de inspeção seguros:
`git status --short`
`git diff --stat`
listagem dos arquivos principais do projeto
Identifique onde estão:
parsers atuais;
writer `EZBookkeepingCSVWriter`;
`AccountMatcher`;
extração de data/mês;
ownership;
regras de pós-processamento;
métodos `convert_*`.
Não comece a refatoração antes de entender o fluxo atual.
Etapa 1 — backup obrigatório
Antes de qualquer alteração de código, crie um backup de consulta do estado atual.
Crie o diretório:
```bash
backup_consulta/estado_atual_YYYYMMDD_HHMMSS/
```
Dentro dele, salve:
cópia de `ofx_converter.py`;
cópia de `services/`;
cópia de `README.md`, se existir;
cópia de `categorias.yaml`, se existir;
cópia de `contas.yaml`, se existir;
cópia de `Dockerfile`, se existir;
cópia de `docker-compose.yml`, se existir;
snapshot de `git status --short` em `git-status.txt`;
snapshot de `git diff --stat` em `git-diff-stat.txt`;
lista de arquivos do projeto em `file-list.txt`.
Regras do backup:
o backup é apenas para consulta;
não altere arquivos dentro dele depois;
não copie dados reais de entrada, saída, logs ou cache;
só inicie a refatoração depois de confirmar que o backup foi criado.
Etapa 2 — criar pipeline comum
Crie:
```text
services/conversion_pipeline.py
```
Responsabilidade do `ConversionPipeline`:
receber `file_path` e um `processor`;
chamar `processor.parse(file_path)`;
validar se há transações;
extrair `month_year`;
criar diretórios necessários em `lido` e `convertido`;
identificar conta via `AccountMatcher`;
aplicar pós-processamento;
escrever CSV via `EZBookkeepingCSVWriter`;
mover arquivo original para `entrada/lido/<month_year>/`;
aplicar ownership quando aplicável;
retornar `True` ou `False`;
centralizar logs comuns.
O pipeline deve receber dependências pelo construtor, por exemplo:
`lido_dir`;
`convertido_dir`;
`date_extractor`;
`account_matcher`;
`postprocessor`;
writer CSV;
callback ou serviço de ownership;
logger, se o projeto já usar logging estruturado.
Evite criar abstrações excessivas. Extraia apenas o fluxo repetido.
Etapa 3 — criar interface de processor
Crie o pacote:
```text
services/processors/
```
Inclua:
```text
services/processors/__init__.py
services/processors/base.py
```
Em `base.py`, crie uma interface simples usando `Protocol` ou classe base leve:
```python
from pathlib import Path
from typing import Protocol

class FileProcessor(Protocol):
    name: str

    def can_handle(self, file_path: Path) -> bool:
        ...

    def parse(self, file_path: Path) -> list[dict]:
        ...
```
Não implemente modelo de domínio novo agora. As transações podem continuar como `dict` para reduzir risco.
Etapa 4 — criar processors/adapters
Crie processors que apenas embrulham os parsers atuais, sem alterar a lógica interna deles.
Criar, conforme existirem parsers correspondentes no projeto:
```text
services/processors/ofx_processor.py
services/processors/mercadopago_processor.py
services/processors/rico_processor.py
services/processors/rico_investimento_processor.py
services/processors/xp_cc_processor.py
services/processors/xp_conta_processor.py
services/processors/bb_processor.py
```
Cada processor deve:
ter atributo `name`;
implementar `can_handle(file_path)`;
implementar `parse(file_path)`;
usar o parser atual;
não duplicar lógica de escrita CSV, movimentação, conta, pasta ou ownership.
Exemplo esperado:
```python
from pathlib import Path

class BBProcessor:
    name = "Banco do Brasil CSV"

    def __init__(self, bb_parser):
        self.bb_parser = bb_parser

    def can_handle(self, file_path: Path) -> bool:
        return self.bb_parser.is_bb_csv(file_path)

    def parse(self, file_path: Path) -> list[dict]:
        return self.bb_parser.parse(str(file_path))
```
Ajuste o exemplo conforme a assinatura real do parser existente.
Etapa 5 — criar registry
Crie:
```text
services/processor_registry.py
```
Responsabilidade do `ProcessorRegistry`:
manter lista ordenada de processors;
encontrar o primeiro processor compatível com o arquivo;
logar qual processor foi selecionado;
evitar listas hardcoded espalhadas em `scan_and_convert`;
permitir obter processor específico por nome/chave para compatibilidade com métodos antigos.
Ordem inicial de detecção:
XP cartão por header;
XP conta por header;
Banco do Brasil por header;
Rico CSV;
Mercado Pago CSV;
OFX/QFX;
Rico/XP investimento XLSX.
A ordem importa porque vários formatos usam `.csv`.
Preferir detecção por header/conteúdo quando o parser atual permitir. Se algum parser só detectar por nome/extensão, mantenha o comportamento atual e documente o risco.
Etapa 6 — extrair pós-processamento
Crie:
```text
services/transaction_postprocessor.py
```
Mova a regra atual de `_postprocess_transactions` para essa classe/serviço.
Regra que deve ser preservada:
se a conta começa com `cc nubank`;
e a descrição é `pagamento recebido`;
então a transação deve virar:
`type = transfer`
`category = Transferência Geral`
`subcategory = Pagamento de Cartão de Crédito`
Não altere a semântica da regra. Apenas mova a responsabilidade.
Se fizer sentido, modele como uma classe simples `TransactionPostProcessor` com método:
```python
def process(self, transactions: list[dict], account_name: str) -> list[dict]:
    ...
```
Não crie uma engine complexa de regras nesta etapa, a menos que o projeto já tenha algo parecido.
Etapa 7 — adaptar `OFXConverter`
Reduza `OFXConverter` para atuar como orquestrador principal.
Ele deve cuidar de:
setup de paths;
setup de logging;
setup de dependências;
criação dos parsers existentes;
criação dos processors;
criação do registry;
criação do pipeline;
`scan_and_convert`;
`watch`;
compatibilidade com métodos públicos antigos.
`scan_and_convert` deve seguir este fluxo:
```python
for file_path in self.entrada_dir.iterdir():
    if file_path.is_dir():
        continue

    processor = self.registry.find(file_path)

    if processor:
        self.pipeline.convert(file_path, processor)
    else:
        logar arquivo ignorado ou não reconhecido
```
Mantenha os métodos públicos antigos:
`convert_file`
`convert_mercadopago_file`
`convert_rico_file`
`convert_xp_cc_file`
`convert_xp_conta_file`
`convert_rico_investimento_file`
`convert_bb_file`
Eles devem virar wrappers que delegam para `pipeline.convert(...)` usando o processor adequado.
Exemplo conceitual:
```python
def convert_bb_file(self, csv_file: Path) -> bool:
    return self.pipeline.convert(csv_file, self.registry.get("bb"))
```
Ajuste nomes e chaves conforme a implementação real.
Etapa 8 — verificação obrigatória
Antes de finalizar, rode no mínimo:
```bash
python -m py_compile ofx_converter.py services/*.py services/processors/*.py
```
Se existirem testes, rode-os.
Se não existirem testes, faça uma verificação manual mínima sem processar arquivos reais sensíveis. Use cópia temporária ou ambiente controlado.
Também verifique:
imports;
inicialização da aplicação;
se Docker continua usando o mesmo entrypoint;
`git diff`;
se arquivos de dados reais não foram alterados indevidamente;
se métodos antigos continuam existindo;
se `ofx_converter.py` ficou menor e mais focado.
Etapa 9 — documentação UML obrigatória
Ao final da implementação, crie na raiz:
```text
UML_ARQUITETURA_FINAL.md
```
O documento deve explicar como o projeto funciona após a refatoração.
Inclua:
Resumo objetivo da nova arquitetura.
Responsabilidade de cada novo módulo.
Diagrama de classes em Mermaid contendo:
`OFXConverter`;
`ConversionPipeline`;
`ProcessorRegistry`;
`FileProcessor`;
processors concretos;
parsers atuais;
`TransactionPostProcessor`;
`AccountMatcher`;
`DateExtractor`, se existir;
`EZBookkeepingCSVWriter`.
Diagrama de sequência em Mermaid mostrando:
`watch`;
`scan_and_convert`;
`registry.find`;
`processor.can_handle`;
`processor.parse`;
`pipeline.convert`;
pós-processamento;
identificação de conta;
escrita CSV;
movimentação para `lido`.
Diagrama de fluxo em Mermaid mostrando decisão por tipo de arquivo.
Lista dos principais métodos chamados em ordem.
Explicação de como adicionar novo banco/formato futuramente.
Mantenha o documento objetivo. Ele deve servir para manutenção futura, não para inflar documentação.
Critérios de aceite
A tarefa só está concluída se:
backup de consulta foi criado antes da refatoração;
`ofx_converter.py` ficou menor e mais focado;
`ConversionPipeline` centraliza o fluxo comum;
processors existem e usam parsers atuais;
`ProcessorRegistry` decide o processor correto;
métodos antigos continuam disponíveis;
CSV gerado mantém header e colunas atuais;
organização por mês permanece igual;
arquivos processados continuam indo para `entrada/lido/<month_year>/`;
logs continuam úteis;
nenhuma pasta pesada/sensível foi copiada ou alterada indevidamente;
verificação com `py_compile` foi executada;
testes existentes foram executados, se houver;
`UML_ARQUITETURA_FINAL.md` foi criado;
`git diff` foi revisado antes da resposta final.
Entrega final obrigatória
Na resposta final, informe:
Arquivos criados.
Arquivos alterados.
Caminho do backup criado.
Resumo da nova arquitetura.
Comandos de verificação executados.
Resultado dos comandos.
Riscos restantes.
Pontos que não foram alterados por decisão de segurança.
Próximos passos recomendados, se houver.
Se algum item não puder ser feito, informe claramente o motivo.
Não diga que algo foi verificado se não foi.
Não oculte falhas de teste, erro de import ou limitação encontrada.