FROM python:3.11-slim

# Instalar dependencias
RUN pip install --no-cache-dir ofxparse pyyaml

# Criar diretorios de trabalho
WORKDIR /app

# Criar diretorios para os arquivos
RUN mkdir -p /app/entrada /app/entrada/lido /app/convertido /app/logs

# Copiar services
COPY services/ /app/services/

# Copiar arquivo de regras de categorizacao
COPY categorias.yaml /app/

# Copiar script principal v3
COPY ofx_converter.py /app/

# Tornar o script executavel
RUN chmod +x /app/ofx_converter.py

# Comando para rodar o conversor v3
CMD ["python", "/app/ofx_converter.py"]
