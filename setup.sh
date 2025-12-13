#!/bin/bash

# Script de inicialização do OFX Converter v2.0

echo "🚀 Configurando OFX Converter v2.0..."

# Criar diretórios necessários
mkdir -p entrada entrada/lido convertido logs

echo "📁 Estrutura de pastas criada:"
echo "   ./entrada/          <- Coloque arquivos .ofx aqui"
echo "   ./entrada/lido/     <- Arquivos processados (organizados por mês-ano)"
echo "   ./convertido/       <- Arquivos .qif convertidos (organizados por mês-ano)"
echo "   ./logs/             <- Logs da aplicação"

# Dar permissões adequadas
chmod -R 755 entrada convertido logs
chmod +x ofx_converter.py

echo ""
echo "✅ Configuração concluída!"
echo ""
echo "🆕 NOVIDADES v2.0:"
echo "   📂 Organização automática por mês-ano (ex: 09-2025)"
echo "   🎯 Categorização inteligente melhorada"
echo "   📊 Extração automática de datas dos arquivos OFX"
echo ""
echo "🐳 Para iniciar o conversor v2.0:"
echo "   docker-compose -f docker-compose.yml up -d"
echo ""
echo "🔍 Para ver logs:"
echo "   docker-compose -f docker-compose.yml logs -f"
echo ""
echo "📋 Para parar:"
echo "   docker-compose -f docker-compose.yml down"
echo ""
echo "📂 Estrutura final:"
echo "   entrada/lido/09-2025/arquivo1.ofx"
echo "   entrada/lido/10-2025/arquivo2.ofx"
echo "   convertido/09-2025/arquivo1.qif"
echo "   convertido/10-2025/arquivo2.qif"
