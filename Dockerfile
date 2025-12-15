FROM python:3.11-slim

# Instalar dependencias
RUN pip install --no-cache-dir ofxparse pyyaml

# Criar diretorios de trabalho
WORKDIR /app

# Criar diretorios para os arquivos
RUN mkdir -p /app/entrada /app/entrada/lido /app/convertido /app/logs

# Nota: Código Python será montado via volumes (docker-compose.yml)
# Isso permite hot reload sem rebuild

# Comando para rodar o conversor
CMD ["python", "/app/ofx_converter.py"]
