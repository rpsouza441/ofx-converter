#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Parser para arquivos CSV da Rico
Formato: Data;Descricao;Valor;Saldo
"""

import csv
import logging
from datetime import datetime
from typing import Dict, List, Any
from services.text_normalizer import TextNormalizer
from services.categorizer import TransactionCategorizer

logger = logging.getLogger(__name__)


class RicoParser:
    """Parser para extratos CSV da Rico"""
    
    def __init__(self, categorizer: TransactionCategorizer):
        self.text_normalizer = TextNormalizer()
        self.categorizer = categorizer
    
    def parse(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Faz parse de arquivo CSV da Rico
        
        Args:
            file_path: Caminho do arquivo CSV
            
        Returns:
            Lista de transações parseadas
        """
        transactions = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                # Detecta se é arquivo Rico pelo header
                first_line = f.readline().strip()
                if not self._is_rico_format(first_line):
                    raise ValueError(f"Arquivo não está no formato Rico. Header: {first_line}")
                
                # Reset para início
                f.seek(0)
                
                reader = csv.DictReader(f, delimiter=';')
                
                for row in reader:
                    try:
                        transaction = self._parse_transaction(row)
                        transactions.append(transaction)
                    except Exception as e:
                        logger.warning(f"Erro ao parsear linha Rico: {e}. Linha: {row}")
                        continue
            
            logger.info(f"Rico: {len(transactions)} transações parseadas de {file_path}")
            return transactions
            
        except Exception as e:
            logger.error(f"Erro ao processar arquivo Rico {file_path}: {e}")
            raise
    
    def _is_rico_format(self, header: str) -> bool:
        """Verifica se é formato Rico pelo header"""
        # Formato antigo: Data;Descricao;Valor;Saldo
        expected_fields_old = ['Data', 'Descricao', 'Valor', 'Saldo']
        # Formato novo: Data;Hora;Descricao;Valor;Saldo
        expected_fields_new = ['Data', 'Hora', 'Descricao', 'Valor', 'Saldo']
        
        header_fields = [f.strip() for f in header.split(';')]
        
        return header_fields == expected_fields_old or header_fields == expected_fields_new
    
    def _parse_transaction(self, row: Dict[str, str]) -> Dict[str, Any]:
        """
        Parseia uma transação da Rico
        """
        # Parse data
        if 'Hora' in row:
             # Formato Novo: Data separada da Hora
             date_str = f"{row['Data'].strip()} {row['Hora'].strip()}"
             try:
                 dt = datetime.strptime(date_str, "%d/%m/%y %H:%M:%S")
                 date = dt.strftime('%Y-%m-%d %H:%M:%S')
             except Exception as e:
                 logger.error(f"Erro ao parsear data/hora Rico '{date_str}': {e}")
                 date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        else:
            # Formato Antigo: "26/11/25 às 14:13:18"
            date_str = row['Data'].strip()
            date = self._parse_date(date_str)
        
        # Parse descrição
        description = self.text_normalizer.normalize_utf8(row['Descricao'].strip())
        
        # Parse valor
        amount = self._parse_amount(row['Valor'].strip())
        
        # Categorizar
        category_info = self.categorizer.categorize_smart(description, amount)
        
        return {
            'date': date,
            'description': description,
            'amount': amount,
            'type': category_info['type'],
            'category': category_info['category'],
            'subcategory': category_info.get('subcategory', ''),
            'balance': self._parse_amount(row['Saldo'].strip())
        }
    
    def _parse_date(self, date_str: str) -> str:
        """
        Parse data da Rico (Formato Antigo): "26/11/25 às 14:13:18"
        """
        try:
            # Remover " às " e parsear
            if ' às ' in date_str:
                date_part, time_part = date_str.split(' às ')
                dt = datetime.strptime(f"{date_part} {time_part}", "%d/%m/%y %H:%M:%S")
                return dt.strftime('%Y-%m-%d %H:%M:%S')
            return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
        except Exception as e:
            logger.error(f"Erro ao parsear data Rico '{date_str}': {e}")
            # Fallback: retorna data atual como string
            return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    def _parse_amount(self, value_str: str) -> float:
        """
        Parse valor da Rico: "R$ 1.000,00" ou "-R$ 300,00"
        
        Args:
            value_str: String de valor
            
        Returns:
            Float com valor
        """
        try:
            # Remover "R$", espaços, e trocar separadores
            clean = value_str.replace('R$', '').strip()
            
            # Verificar sinal negativo
            is_negative = clean.startswith('-')
            clean = clean.replace('-', '').strip()
            
            # Remover pontos (milhares) e trocar vírgula por ponto (decimais)
            clean = clean.replace('.', '').replace(',', '.')
            
            amount = float(clean)
            
            return -amount if is_negative else amount
            
        except Exception as e:
            logger.error(f"Erro ao parsear valor Rico '{value_str}': {e}")
            return 0.0
    
