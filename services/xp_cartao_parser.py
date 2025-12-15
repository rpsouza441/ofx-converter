#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Parser para arquivos CSV de cartão de crédito da XP
Formato: Data;Estabelecimento;Portador;Valor;Parcela
"""

import csv
import logging
from datetime import datetime
from typing import Dict, List, Any
from services.text_normalizer import TextNormalizer
from services.categorizer import TransactionCategorizer

logger = logging.getLogger(__name__)


class XPCartaoParser:
    """Parser para extratos CSV de cartão de crédito da XP"""
    
    def __init__(self, categorizer: TransactionCategorizer):
        self.text_normalizer = TextNormalizer()
        self.categorizer = categorizer
    
    def parse(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Faz parse de arquivo CSV do cartão XP
        
        Args:
            file_path: Caminho do arquivo CSV
            
        Returns:
            Lista de transações parseadas
        """
        transactions = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter=';')
                
                for row in reader:
                    try:
                        transaction = self._parse_transaction(row)
                        if transaction:
                            transactions.append(transaction)
                    except Exception as e:
                        logger.warning(f"Erro ao parsear linha XP: {e}. Linha: {row}")
                        continue
            
            logger.info(f"XP Cartão: {len(transactions)} transações parseadas de {file_path}")
            return transactions
            
        except Exception as e:
            logger.error(f"Erro ao processar arquivo XP {file_path}: {e}")
            raise
    
    def _parse_transaction(self, row: Dict[str, str]) -> Dict[str, Any]:
        """
        Parseia uma transação do cartão XP
        
        Formato esperado:
        Data: "03/07/2025"
        Estabelecimento: "MOVEIS VALVERDE"
        Portador: "CARINE PEREIRA"
        Valor: "R$ 99,50" ou "R$ -3.472,34"
        Parcela: "5 de 6" ou "-"
        """
        # Parse data
        date_str = self._parse_date(row['Data'].strip())
        
        # Parse descrição (Estabelecimento + Portador se relevante)
        estabelecimento = row['Estabelecimento'].strip()
        portador = row['Portador'].strip()
        parcela = row['Parcela'].strip()
        
        # Montar descrição
        description = estabelecimento
        if parcela and parcela != '-':
            description = f"{estabelecimento} - Parcela {parcela}"
        
        # Normalizar
        description = self.text_normalizer.normalize_utf8(description)
        
        # Parse valor
        amount = self._parse_amount(row['Valor'].strip())
        
        # Categorizar
        category_info = self.categorizer.categorize_smart(description, amount)
        
        return {
            'date': date_str,
            'description': description,
            'amount': amount,
            'type': category_info['type'],
            'category': category_info['category'],
            'subcategory': category_info.get('subcategory', ''),
            'qif_category': self._get_qif_category(category_info),
            'portador': portador  # Info adicional
        }
    
    def _parse_date(self, date_str: str) -> str:
        """
        Parse data: "03/07/2025" -> "2025-07-03 00:00:00"
        
        Args:
            date_str: String de data
            
        Returns:
            String no formato 'YYYY-MM-DD 00:00:00'
        """
        try:
            dt = datetime.strptime(date_str, '%d/%m/%Y')
            return dt.strftime('%Y-%m-%d 00:00:00')
        except Exception as e:
            logger.error(f"Erro ao parsear data XP '{date_str}': {e}")
            return datetime.now().strftime('%Y-%m-%d 00:00:00')
    
    def _parse_amount(self, value_str: str) -> float:
        """
        Parse valor: "R$ 99,50" ou "R$ -3.472,34"
        
        Args:
            value_str: String de valor
            
        Returns:
            Float com valor
        """
        try:
            # Remover "R$" e espaços
            clean = value_str.replace('R$', '').strip()
            
            # Verificar sinal negativo
            is_negative = clean.startswith('-')
            clean = clean.replace('-', '').strip()
            
            # Remover pontos (milhares) e trocar vírgula por ponto (decimais)
            clean = clean.replace('.', '').replace(',', '.')
            
            amount = float(clean)
            
            # XP: valores positivos = despesas, negativos = pagamentos
            # Inverter sinal para pagamentos ficarem positivos (income)
            if is_negative:
                return amount  # Pagamento (positivo = income)
            else:
                return -amount  # Despesa (negativo = expense)
            
        except Exception as e:
            logger.error(f"Erro ao parsear valor XP '{value_str}': {e}")
            return 0.0
    
    def _get_qif_category(self, category_info: dict) -> str:
        """
        Gera categoria QIF com base no tipo
        
        Args:
            category_info: Dict com type, category, subcategory
            
        Returns:
            String de categoria QIF
        """
        if category_info['type'] == 'transfer':
            return f"[{category_info['category']}]"
        else:
            return category_info['category']
    
    @staticmethod
    def is_xp_cartao_csv(file_path) -> bool:
        """
        Verifica se é CSV do cartão XP pelo header
        
        Args:
            file_path: Path do arquivo
            
        Returns:
            True se for CSV XP
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
                expected_header = 'Data;Estabelecimento;Portador;Valor;Parcela'
                return first_line == expected_header
        except:
            return False
