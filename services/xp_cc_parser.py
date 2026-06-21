#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XP Credit Card CSV Parser Service
Responsável por parsear arquivos CSV de fatura de cartão de crédito do XP
"""

import csv
import re
import logging
import calendar
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class XPCCParser:
    """Parser de arquivos CSV de fatura XP Credit Card"""
    
    # Identificador único do CSV do XP CC
    EXPECTED_HEADER = "Data;Estabelecimento;Portador;Valor;Parcela"
    
    def __init__(self, text_normalizer, categorizer, date_extractor):
        """
        Inicializa o parser com dependências
        
        Args:
            text_normalizer: Serviço de normalização de texto
            categorizer: Serviço de categorização
            date_extractor: Serviço de extração de datas
        """
        self.text_normalizer = text_normalizer
        self.categorizer = categorizer
        self.date_extractor = date_extractor
    
    @staticmethod
    def is_xp_cc_csv(file_path: Path) -> bool:
        """
        Verifica se o arquivo é um CSV de fatura do XP CC
        
        Args:
            file_path: Path do arquivo CSV
            
        Returns:
            True se for CSV de fatura do XP CC
        """
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                # Primeira linha deve conter o cabeçalho
                # utf-8-sig automaticamente remove BOM se presente
                header = f.readline().strip()
                return header == XPCCParser.EXPECTED_HEADER
        except Exception as e:
            logger.debug(f"Erro ao verificar CSV XP CC: {e}")
            return False
    
    def parse_csv(self, file_path: Path) -> Optional[List[Dict]]:
        """
        Parse do arquivo CSV de fatura XP CC
        
        Args:
            file_path: Path do arquivo CSV
            
        Returns:
            Lista de transações ou None se falhar
        """
        try:
            transactions = []
            invoice_reference = self._extract_invoice_reference_from_filename(file_path.name)
            
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                # Ler cabeçalho (utf-8-sig remove BOM automaticamente)
                header = f.readline().strip()
                if header != self.EXPECTED_HEADER:
                    logger.error(f"Cabeçalho CSV inválido: {header}")
                    return None
                
                # Processar transações
                csv_reader = csv.DictReader(f, delimiter=';', fieldnames=[
                    'Data', 'Estabelecimento', 'Portador', 'Valor', 'Parcela'
                ])
                
                for row in csv_reader:
                    # Pular linhas vazias
                    if not row.get('Data') or not row['Data'].strip():
                        continue
                    
                    transaction = self._parse_transaction(row, invoice_reference)
                    if transaction:
                        transactions.append(transaction)
            
            logger.info(f"Parse XP CC concluído: {len(transactions)} transações")
            return transactions if transactions else None
            
        except Exception as e:
            logger.error(f"Erro no parse CSV XP CC: {e}")
            return None
    
    def _parse_transaction(
        self,
        row: Dict[str, str],
        invoice_reference: Optional[datetime] = None
    ) -> Optional[Dict]:
        """
        Processa uma linha de transação do CSV
        
        Args:
            row: Dicionário com dados da linha
            
        Returns:
            Dicionário com transação formatada ou None se inválida
        """
        try:
            # Extrair e converter data (DD/MM/YYYY -> YYYY-MM-DD)
            date_str = row['Data'].strip()
            date_obj = self._parse_date(date_str)
            if not date_obj:
                logger.warning(f"Data inválida: {date_str}")
                return None
            
            # Extrair estabelecimento e portador
            estabelecimento = row['Estabelecimento'].strip()
            portador = row['Portador'].strip()
            parcela_info = row['Parcela'].strip()
            
            if not estabelecimento:
                logger.warning("Estabelecimento vazio, pulando transação")
                return None

            date_obj = self._adjust_installment_date(
                date_obj,
                parcela_info,
                invoice_reference
            )
            date = date_obj.strftime('%Y-%m-%d 00:00:00')
            
            # Construir descrição
            description = self._build_description(portador, estabelecimento, parcela_info)
            
            # Normalizar descrição
            description = self.text_normalizer.normalize_utf8(description)
            description = self.text_normalizer.clean_memo(description)
            
            # Extrair e converter valor (formato BR: R$ 1.000,00 -> US: 1000.00)
            amount_str = row['Valor'].strip()
            amount = self._convert_amount(amount_str)
            
            # Determinar categoria
            cat_info = self._categorize_transaction(description, amount)
            
            return {
                'date': date,
                'amount': str(amount),
                'description': description,
                'type': cat_info['type'],
                'category': cat_info['category'],
                'subcategory': cat_info['subcategory']
            }
            
        except Exception as e:
            logger.error(f"Erro ao processar transação: {e}")
            return None
    
    def _build_description(self, portador: str, estabelecimento: str, parcela_info: str) -> str:
        """
        Constrói a descrição da transação
        
        Args:
            portador: Nome do portador do cartão
            estabelecimento: Nome do estabelecimento
            parcela_info: Informação de parcela ("5 de 6", "-", " de 1", etc.)
            
        Returns:
            String formatada da descrição
        """
        # Começar com portador e estabelecimento
        if portador:
            description = f"{portador} - {estabelecimento}"
        else:
            description = estabelecimento
        
        # Adicionar informação de parcela se existir e não for "-" ou vazio
        if parcela_info and parcela_info != '-' and parcela_info.strip():
            # Limpar " de 1" (parcela única não precisa ser mostrada)
            if parcela_info.strip() != 'de 1' and not parcela_info.strip().endswith('de 1'):
                # Converter "5 de 6" para "(parcela 5/6)"
                parcela_clean = parcela_info.replace(' de ', '/')
                description += f" (parcela {parcela_clean})"
        
        return description
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """
        Converte data de DD/MM/YYYY para YYYY-MM-DD HH:MM:SS
        
        Args:
            date_str: Data no formato DD/MM/YYYY
            
        Returns:
            Data no formato YYYY-MM-DD HH:MM:SS ou None se inválida
        """
        try:
            return datetime.strptime(date_str, '%d/%m/%Y')
        except ValueError:
            return None

    def _convert_date(self, date_str: str) -> Optional[str]:
        """
        Converte data de DD/MM/YYYY para YYYY-MM-DD HH:MM:SS.
        Mantido para compatibilidade com chamadas externas.
        """
        date_obj = self._parse_date(date_str)
        if not date_obj:
            return None
        return date_obj.strftime('%Y-%m-%d 00:00:00')

    def _extract_invoice_reference_from_filename(self, filename: str) -> Optional[datetime]:
        """
        Extrai a competência da fatura XP a partir do vencimento no nome.

        Exemplo: Fatura2026-03-15 representa a fatura de 02-2026.
        """
        match = re.search(r'(20\d{2})[-_]?(\d{2})[-_]?(\d{2})', filename)
        if not match:
            logger.warning(f"Nao foi possivel extrair vencimento da fatura XP: {filename}")
            return None

        due_year = int(match.group(1))
        due_month = int(match.group(2))

        if due_month == 1:
            return datetime(due_year - 1, 12, 1)
        return datetime(due_year, due_month - 1, 1)

    def _is_multi_installment(self, parcela_info: str) -> bool:
        """Retorna True para parcelas do tipo '3 de 10'."""
        if not parcela_info:
            return False

        match = re.search(r'(\d+)\s+de\s+(\d+)', parcela_info.strip(), re.IGNORECASE)
        if not match:
            return False

        total_installments = int(match.group(2))
        return total_installments > 1

    def _adjust_installment_date(
        self,
        purchase_date: datetime,
        parcela_info: str,
        invoice_reference: Optional[datetime]
    ) -> datetime:
        """
        Parcelas na XP vêm com a data original da compra.
        Para importação financeira, a parcela pertence à competência da fatura.
        """
        if not invoice_reference or not self._is_multi_installment(parcela_info):
            return purchase_date

        if (
            purchase_date.year == invoice_reference.year
            and purchase_date.month == invoice_reference.month
        ):
            return purchase_date

        last_day = calendar.monthrange(invoice_reference.year, invoice_reference.month)[1]
        adjusted_day = min(purchase_date.day, last_day)

        logger.info(
            "XP CC: parcela '%s' ajustada de %s para competencia %02d-%04d",
            parcela_info,
            purchase_date.strftime('%Y-%m-%d'),
            invoice_reference.month,
            invoice_reference.year
        )

        return purchase_date.replace(
            year=invoice_reference.year,
            month=invoice_reference.month,
            day=adjusted_day
        )
    
    def _convert_amount(self, amount_str: str) -> float:
        """
        Converte valor do formato brasileiro para float
        
        Args:
            amount_str: Valor no formato brasileiro (R$ 1.000,00 ou R$ -1.000,00)
            
        Returns:
            Valor como float
        """
        try:
            # Remover "R$" e espaços
            clean = amount_str.replace('R$', '').strip()
            
            # Verificar sinal negativo
            is_negative = clean.startswith('-')
            if is_negative:
                clean = clean.replace('-', '').strip()
            
            # Remover pontos de milhar e trocar vírgula por ponto
            clean = clean.replace('.', '').replace(',', '.')
            
            amount = float(clean)
            
            return -amount if is_negative else amount
            
        except ValueError:
            logger.warning(f"Valor inválido: {amount_str}, usando 0.00")
            return 0.0
    
    def _categorize_transaction(self, description: str, amount: float) -> dict:
        """
        Categoriza transação usando o fluxo inteligente do categorizer.
        
        Args:
            description: Descrição da transação
            amount: Valor da transação (negativo = estorno/pagamento)
            
        Returns:
            Dict com type, category, subcategory
        """
        # O parser de fatura XP usa:
        # - valor positivo para compras (despesa)
        # - valor negativo para pagamento/estorno
        # Já o categorizer espera:
        # - valor negativo para despesa
        # - valor positivo para receita/transferência
        categorizer_amount = -amount
        cat_info = self.categorizer.categorize_smart(description, categorizer_amount)

        return {
            'type': cat_info['type'],
            'category': cat_info['category'],
            'subcategory': cat_info.get('subcategory', '')
        }
    
    def get_date_for_filename(self, file_path: Path) -> Optional[str]:
        """
        Extrai a data da primeira transação para usar no nome do arquivo
        
        Args:
            file_path: Path do arquivo CSV
            
        Returns:
            Data no formato DD-MM-YYYY ou None
        """
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                # Pular cabeçalho (utf-8-sig remove BOM)
                f.readline()
                
                # Ler primeira transação
                csv_reader = csv.DictReader(f, delimiter=';', fieldnames=[
                    'Data', 'Estabelecimento', 'Portador', 'Valor', 'Parcela'
                ])
                
                for row in csv_reader:
                    date_str = row.get('Data', '').strip()
                    if date_str:
                        # Converter DD/MM/YYYY para DD-MM-YYYY
                        return date_str.replace('/', '-')
                
            return None
            
        except Exception as e:
            logger.error(f"Erro ao extrair data do arquivo: {e}")
            return None
