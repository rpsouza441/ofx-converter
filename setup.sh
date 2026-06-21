#!/bin/bash

# Script de inicialização do OFX Converter

echo "Configurando OFX Converter..."

# Criar diretórios necessários
mkdir -p entrada entrada/lido convertido logs

echo "Estrutura de pastas criada:"
echo "   ./entrada/          <- Coloque arquivos OFX/QFX/CSV/XLSX suportados aqui"
echo "   ./entrada/lido/     <- Arquivos processados (organizados por mês-ano)"
echo "   ./convertido/       <- Arquivos .csv para ezBookkeeping (organizados por mês-ano)"
echo "   ./logs/             <- Logs da aplicação"
echo ""
echo "Mapeamento no container via docker-compose.yml:"
echo "   ./entrada           -> /app/entrada"
echo "   ./entrada/lido      -> /app/entrada/lido"
echo "   ./convertido        -> /app/convertido"
echo "   ./logs              -> /app/logs"
echo "   ./ofx_converter.py  -> /app/ofx_converter.py"
echo "   ./services          -> /app/services"
echo "   ./categorias.yaml   -> /app/categorias.yaml"
echo "   ./contas.yaml       -> /app/contas.yaml"

# Dar permissões adequadas
chmod -R 755 entrada convertido logs
chmod +x ofx_converter.py

echo ""
echo "Configuração concluída."
echo ""
echo "Recursos atuais:"
echo "   Organização automática por mês-ano (ex: 09-2025)"
echo "   Categorização via categorias.yaml"
echo "   Identificação de contas via contas.yaml"
echo "   Conversão para CSV compatível com ezBookkeeping"
echo "   Arquitetura com pipeline e processors por banco/formato"
echo ""
echo "Para iniciar o conversor:"
echo "   docker compose up -d"
echo ""
echo "Para ver logs:"
echo "   docker compose logs -f"
echo ""
echo "Para parar:"
echo "   docker compose down"
echo ""
echo "Para rebuildar:"
echo "   docker compose down"
echo "   docker compose build --no-cache"
echo "   docker compose up -d"
echo ""
echo "Estrutura final esperada:"
echo "   entrada/lido/09-2025/arquivo1.ofx"
echo "   entrada/lido/10-2025/arquivo2.csv"
echo "   convertido/09-2025/arquivo1.csv"
echo "   convertido/10-2025/arquivo2.csv"
