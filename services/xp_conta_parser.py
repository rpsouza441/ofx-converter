#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XP Conta Digital CSV Parser Service
Responsável por parsear arquivos CSV de extrato da conta digital XP
"""

import csv
import re
import logging
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class XPContaParser:
    """Parser de arquivos CSV de extrato da conta digital XP"""
    
    # Identificador único do CSV da Conta XP
    EXPECTED_HEADER = "Data;Descricao;Valor;Saldo"
    
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
    def is_xp_conta_csv(file_path: Path) -> bool:
        """
        Verifica se o arquivo é um CSV de extrato da conta digital XP
        
        Args:
            file_path: Path do arquivo CSV
            
        Returns:
            True se for CSV de extrato da conta digital XP
        """
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                header = f.readline().strip()
                return header == XPContaParser.EXPECTED_HEADER
        except Exception as e:
            logger.debug(f"Erro ao verificar CSV XP Conta: {e}")
            return False
    
    def parse_csv(self, file_path: Path) -> Optional[List[Dict]]:
        """
        Parse do arquivo CSV de extrato da conta digital XP
        
        Args:
            file_path: Path do arquivo CSV
            
        Returns:
            Lista de transações ou None se falhar
        """
        try:
            transactions = []
            
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                header = f.readline().strip()
                if header != self.EXPECTED_HEADER:
                    logger.error(f"Cabeçalho CSV inválido: {header}")
                    return None
                
                csv_reader = csv.DictReader(f, delimiter=';', fieldnames=[
                    'Data', 'Descricao', 'Valor', 'Saldo'
                ])
                
                for row in csv_reader:
                    if not row.get('Data') or not row['Data'].strip():
                        continue
                    
                    transaction = self._parse_transaction(row)
                    if transaction:
                        transactions.append(transaction)
            
            logger.info(f"Parse XP Conta concluído: {len(transactions)} transações")
            return transactions if transactions else None
            
        except Exception as e:
            logger.error(f"Erro no parse CSV XP Conta: {e}")
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
            # Extrair e converter data (DD/MM/YY às HH:MM:SS -> YYYY-MM-DD HH:MM:SS)
            date_str = row['Data'].strip()
            date = self._convert_date(date_str)
            if not date:
                logger.warning(f"Data inválida: {date_str}")
                return None
            
            # Extrair descrição
            description = row['Descricao'].strip()
            if not description:
                logger.warning("Descrição vazia, pulando transação")
                return None
            
            # Normalizar descrição
            description = self.text_normalizer.normalize_utf8(description)
            description = self.text_normalizer.clean_memo(description)
            
            # Extrair e converter valor
            amount_str = row['Valor'].strip()
            amount = self._convert_amount(amount_str)
            
            # Categorizar transação
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
    
    def _convert_date(self, date_str: str) -> Optional[str]:
        """
        Converte data de DD/MM/YY às HH:MM:SS para YYYY-MM-DD HH:MM:SS
        
        Args:
            date_str: Data no formato DD/MM/YY às HH:MM:SS
            
        Returns:
            Data no formato YYYY-MM-DD HH:MM:SS ou None se inválida
        """
        try:
            # Formato: "13/12/25 às 09:02:56"
            # Remover " às " e substituir por espaço
            clean_date = date_str.replace(' às ', ' ')
            
            # Parse DD/MM/YY HH:MM:SS
            dt = datetime.strptime(clean_date, '%d/%m/%y %H:%M:%S')
            
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except ValueError as e:
            logger.debug(f"Erro ao converter data '{date_str}': {e}")
            return None
    
    def _convert_amount(self, amount_str: str) -> float:
        """
        Converte valor do formato brasileiro para float
        
        Args:
            amount_str: Valor no formato brasileiro (R$ 1.000,00 ou -R$ 1.000,00)
            
        Returns:
            Valor como float
        """
        try:
            # Remover "R$" e espaços
            clean = amount_str.replace('R$', '').strip()
            
            # Verificar sinal negativo (pode estar antes ou depois do R$)
            is_negative = '-' in clean
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
        Categoriza transação usando categorize_smart do categorizer
        
        Args:
            description: Descrição da transação
            amount: Valor da transação
            
        Returns:
            Dict com type, category, subcategory, qif_category
        """
        # Usar categorize_smart que já considera o sinal do valor
        return self.categorizer.categorize_smart(description, amount)
