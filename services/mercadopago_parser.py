#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mercado Pago CSV Parser Service
Responsável por parsear arquivos CSV exportados do Mercado Pago e gerar transações para QIF
"""

import csv
import re
import logging
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class MercadoPagoParser:
    """Parser de arquivos CSV do Mercado Pago com suporte a transferências Pix"""
    
    # Identificador único do CSV do Mercado Pago
    EXPECTED_HEADER = "RELEASE_DATE;TRANSACTION_TYPE;REFERENCE_ID;TRANSACTION_NET_AMOUNT;PARTIAL_BALANCE"
    
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
    def is_mercadopago_csv(file_path: Path) -> bool:
        """
        Verifica se o arquivo é um CSV do Mercado Pago
        
        Args:
            file_path: Path do arquivo CSV
            
        Returns:
            True se for CSV do Mercado Pago
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                # Pular primeiras 3 linhas (resumo)
                for _ in range(3):
                    f.readline()
                # Linha 4 deve conter o cabeçalho
                header = f.readline().strip()
                return header == MercadoPagoParser.EXPECTED_HEADER
        except Exception as e:
            logger.debug(f"Erro ao verificar CSV Mercado Pago: {e}")
            return False
    
    def parse_csv(self, file_path: Path) -> Optional[List[Dict]]:
        """
        Parse do arquivo CSV do Mercado Pago
        
        Args:
            file_path: Path do arquivo CSV
            
        Returns:
            Lista de transações ou None se falhar
        """
        try:
            transactions = []
            
            with open(file_path, 'r', encoding='utf-8') as f:
                # Pular primeiras 3 linhas (resumo com saldo inicial/final)
                for _ in range(3):
                    f.readline()
                
                # Ler cabeçalho
                header = f.readline().strip()
                if header != self.EXPECTED_HEADER:
                    logger.error(f"Cabeçalho CSV inválido: {header}")
                    return None
                
                # Processar transações
                csv_reader = csv.DictReader(f, delimiter=';', fieldnames=[
                    'RELEASE_DATE', 'TRANSACTION_TYPE', 'REFERENCE_ID', 
                    'TRANSACTION_NET_AMOUNT', 'PARTIAL_BALANCE'
                ])
                
                for row in csv_reader:
                    # Pular linhas vazias
                    if not row.get('RELEASE_DATE') or not row['RELEASE_DATE'].strip():
                        continue
                    
                    transaction = self._parse_transaction(row)
                    if transaction:
                        transactions.append(transaction)
            
            logger.info(f"Parse Mercado Pago concluído: {len(transactions)} transações")
            return transactions if transactions else None
            
        except Exception as e:
            logger.error(f"Erro no parse CSV Mercado Pago: {e}")
            return None
    
    def _parse_transaction(self, row: Dict[str, str]) -> Optional[Dict]:
        """
        Processa uma linha de transação do CSV
        
        Args:
            row: Dicionário com dados da linha
            
        Returns:
            Dicionário com transação formatada ou None se inválida
        """
        try:
            # Extrair e converter data (DD-MM-YYYY -> YYYY-MM-DD)
            date_str = row['RELEASE_DATE'].strip()
            date = self._convert_date(date_str)
            if not date:
                logger.warning(f"Data inválida: {date_str}")
                return None
            
            # Extrair descrição
            description = row['TRANSACTION_TYPE'].strip()
            if not description:
                logger.warning("Descrição vazia, pulando transação")
                return None
            
            # Normalizar descrição
            description = self.text_normalizer.normalize_utf8(description)
            description = self.text_normalizer.clean_memo(description)
            
            # Extrair e converter valor (formato BR: 1.000,00 -> US: 1000.00)
            amount_str = row['TRANSACTION_NET_AMOUNT'].strip()
            amount = self._convert_amount(amount_str)
            
            # Determinar categoria (com detecção de transferências Pix)
            cat_info = self._categorize_transaction(description, amount)
            
            return {
                'date': date,
                'amount': str(amount),
                'description': description,
                'type': cat_info['type'],
                'category': cat_info['category'],
                'subcategory': cat_info['subcategory'],
                'qif_category': cat_info['qif_category']
            }
            
        except Exception as e:
            logger.error(f"Erro ao processar transação: {e}")
            return None
    
    def _convert_date(self, date_str: str) -> Optional[str]:
        """
        Converte data de DD-MM-YYYY para YYYY-MM-DD
        
        Args:
            date_str: Data no formato DD-MM-YYYY
            
        Returns:
            Data no formato YYYY-MM-DD ou None se inválida
        """
        try:
            # Parse DD-MM-YYYY
            dt = datetime.strptime(date_str, '%d-%m-%Y')
            # Retornar YYYY-MM-DD
            return dt.strftime('%Y-%m-%d')
        except ValueError:
            return None
    
    def _convert_amount(self, amount_str: str) -> float:
        """
        Converte valor do formato brasileiro para float
        
        Args:
            amount_str: Valor no formato brasileiro (1.000,00)
            
        Returns:
            Valor como float
        """
        try:
            # Remover pontos de milhar e trocar vírgula por ponto
            amount_clean = amount_str.replace('.', '').replace(',', '.')
            return float(amount_clean)
        except ValueError:
            logger.warning(f"Valor inválido: {amount_str}, usando 0.00")
            return 0.0
    
    def _categorize_transaction(self, description: str, amount: float) -> dict:
        """
        Categoriza transação com detecção especial para transferências Pix
        
        Args:
            description: Descrição da transação
            amount: Valor da transação
            
        Returns:
            Dict com type, category, subcategory, qif_category
        """
        description_lower = description.lower()
        
        # Detectar transferências Pix
        if 'transferência pix' in description_lower or 'transferencia pix' in description_lower:
            category, subcategory = self.categorizer.categorize_transfer(description)
            return {
                'type': 'transfer',
                'category': category,
                'subcategory': subcategory,
                'qif_category': '[Transferências]'  # QIF usa bracket notation
            }
        
        # Para outras transações, usar categorizador normal
        category = self.categorizer.categorize(description, amount)
        
        if amount > 0:
            return {
                'type': 'income',
                'category': category,
                'subcategory': '',
                'qif_category': category
            }
        else:
            return {
                'type': 'expense',
                'category': category,
                'subcategory': '',
                'qif_category': category
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
            with open(file_path, 'r', encoding='utf-8') as f:
                # Pular primeiras 3 linhas (resumo)
                for _ in range(3):
                    f.readline()
                
                # Pular cabeçalho
                f.readline()
                
                # Ler primeira transação
                csv_reader = csv.DictReader(f, delimiter=';', fieldnames=[
                    'RELEASE_DATE', 'TRANSACTION_TYPE', 'REFERENCE_ID', 
                    'TRANSACTION_NET_AMOUNT', 'PARTIAL_BALANCE'
                ])
                
                for row in csv_reader:
                    date_str = row.get('RELEASE_DATE', '').strip()
                    if date_str:
                        return date_str  # Retornar no formato DD-MM-YYYY
                
            return None
            
        except Exception as e:
            logger.error(f"Erro ao extrair data do arquivo: {e}")
            return None
