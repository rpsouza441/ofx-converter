#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Parser para arquivos CSV do Banco do Brasil
Formato: "Data","Lançamento","Detalhes","Nº documento","Valor","Tipo Lançamento"
Encoding: ISO-8859-1 (Latin-1)
"""

import csv
import logging
from datetime import datetime
from typing import Dict, List, Any
from services.text_normalizer import TextNormalizer
from services.categorizer import TransactionCategorizer

logger = logging.getLogger(__name__)


class BBParser:
    """Parser para extratos CSV do Banco do Brasil"""
    
    def __init__(self, categorizer: TransactionCategorizer):
        self.text_normalizer = TextNormalizer()
        self.categorizer = categorizer
    
    @staticmethod
    def is_bb_csv(file_path) -> bool:
        """
        Verifica se é um arquivo CSV do BB lendo o header com encoding latin1
        """
        try:
            with open(file_path, 'r', encoding='latin1') as f:
                header = f.readline().strip()
                # Verifica colunas chaves
                return '"Data"' in header and '"Lançamento"' in header and '"Valor"' in header
        except Exception:
            return False

    def parse(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Faz parse de arquivo CSV do Banco do Brasil
        
        Args:
            file_path: Caminho do arquivo CSV
            
        Returns:
            Lista de transações parseadas
        """
        transactions = []
        
        try:
            with open(file_path, 'r', encoding='latin1') as f:
                # Ler com DictReader
                reader = csv.DictReader(f)
                
                for row in reader:
                    try:
                        # Pular linhas de saldo inicial/anterior se necessário
                        # Mas vamos tentar processar tudo que parece transação
                        if not row['Data'] or not row['Valor']:
                            continue

                        # Se for saldo anterior, ignorar
                        if "Saldo Anterior" in row.get('Lançamento', ''):
                            continue
                            
                        transaction = self._parse_transaction(row)
                        if transaction:
                            transactions.append(transaction)
                    except Exception as e:
                        logger.warning(f"Erro ao parsear linha BB: {e}. Linha: {row}")
                        continue
            
            logger.info(f"BB: {len(transactions)} transações parseadas de {file_path}")
            return transactions
            
        except Exception as e:
            logger.error(f"Erro ao processar arquivo BB {file_path}: {e}")
            raise
    
    def _parse_transaction(self, row: Dict[str, str]) -> Dict[str, Any]:
        """
        Parseia uma transação do BB
        """
        # Parse data
        date_str = row['Data'].strip()
        date = self._parse_date(date_str)
        
        # Parse descrição (Junta Lançamento + Detalhes)
        lancamento = row.get('Lançamento', '').strip()
        detalhes = row.get('Detalhes', '').strip()
        full_desc = f"{lancamento} {detalhes}".strip()
        
        description = self.text_normalizer.normalize_utf8(full_desc)
        
        # Parse valor
        amount = self._parse_amount(row['Valor'].strip())
        
        # Se valor for zero (ex: apenas informativo), ignorar? 
        # Manteremos mesmo zero
        
        # Categorizar
        category_info = self.categorizer.categorize_smart(description, amount)
        
        return {
            'date': date,
            'description': description,
            'amount': amount,
            'type': category_info['type'],
            'category': category_info['category'],
            'subcategory': category_info.get('subcategory', ''),
            'balance': 0.0 # BB CSV não traz saldo linha a linha de forma simples nesta exportação
        }
    
    def _parse_date(self, date_str: str) -> str:
        """
        Parse data do BB: "12/01/2026"
        """
        try:
            dt = datetime.strptime(date_str, "%d/%m/%Y")
            return dt.strftime('%Y-%m-%d 12:00:00') # Fixa meio dia pois não tem hora
        except Exception as e:
            logger.error(f"Erro ao parsear data BB '{date_str}': {e}")
            return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    def _parse_amount(self, value_str: str) -> float:
        """
        Parse valor do BB: "4.152,87" ou "-1.957,48"
        """
        try:
            # Remover pontos (milhares) e trocar vírgula por ponto (decimais)
            clean = value_str.replace('.', '').replace(',', '.')
            return float(clean)
        except Exception as e:
            logger.error(f"Erro ao parsear valor BB '{value_str}': {e}")
            return 0.0
    
