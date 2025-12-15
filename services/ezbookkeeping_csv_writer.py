#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EZBookkeeping CSV Writer Service
Responsável por escrever arquivos CSV no formato do ezBookkeeping
"""

import csv
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class EZBookkeepingCSVWriter:
    """Escreve arquivos CSV no formato do ezBookkeeping"""
    
    # Cabeçalho CSV do ezBookkeeping
    HEADER = [
        'Time', 'Timezone', 'Type', 'Category', 'Sub Category',
        'Account', 'Account Currency', 'Amount',
        'Account2', 'Account2 Currency', 'Account2 Amount',
        'Geographic Location', 'Tags', 'Description'
    ]
    
    def __init__(self, account_name='MercadoPago', currency='BRL', timezone='-03:00'):
        """
        Inicializa o escritor CSV
        
        Args:
            account_name: Nome da conta principal (ex: 'MercadoPago Rodrigo')
            currency: Moeda (default: BRL)
            timezone: Timezone (default: -03:00)
        """
        self.account_name = account_name
        self.currency = currency
        self.timezone = timezone
        self.file = None
        self.writer = None
    
    def create_csv_file(self, filepath: Path):
        """
        Cria arquivo CSV e escreve cabeçalho
        
        Args:
            filepath: Path do arquivo CSV
        """
        try:
            self.file = open(filepath, 'w', newline='', encoding='utf-8')
            self.writer = csv.writer(self.file)
            self.writer.writerow(self.HEADER)
            logger.debug(f"Arquivo CSV criado: {filepath}")
        except Exception as e:
            logger.error(f"Erro ao criar arquivo CSV: {e}")
            raise
    
    def write_transfer(self, date, amount: str, description: str,
                      category: str = 'Transferência Geral',
                      subcategory: str = 'Transferência Bancária',
                      tags: str = ''):
        """
        Escreve uma transação de transferência
        
        Args:
            date: datetime object ou string YYYY-MM-DD HH:MM:SS
            amount: Valor (positivo)
            description: Descrição da transferência
            category: Categoria (default: Transferência Geral)
            subcategory: Subcategoria (default: Transferência Bancária)
            tags: Tags opcionais
        
        Note: Account e Account2 ficam vazios para preenchimento manual
        """
        # Date já vem como string 'YYYY-MM-DD' ou 'YYYY-MM-DD HH:MM:SS'
        time_str = str(date)
        
        # Valor absoluto para transferências
        amount_val = abs(float(amount))
        
        row = [
            time_str,                    # Time
            self.timezone,               # Timezone
            'Transfer',                  # Type
            category,                    # Category
            subcategory,                 # Sub Category
            '',                          # Account (vazio - usuário preenche)
            self.currency,               # Account Currency
            f"{amount_val:.2f}",        # Amount
            '',                          # Account2 (vazio - usuário preenche)
            self.currency,               # Account2 Currency
            f"{amount_val:.2f}",        # Account2 Amount
            '',                          # Geographic Location
            tags,                        # Tags
            description                  # Description
        ]
        
        self.writer.writerow(row)
    
    def write_expense(self, date, amount: str, description: str,
                     category: str, subcategory: str = '', tags: str = ''):
        """
        Escreve uma transação de despesa
        
        Args:
            date: datetime object ou string YYYY-MM-DD HH:MM:SS
            amount: Valor (negativo)
            description: Descrição da despesa
            category: Categoria da despesa
            subcategory: Subcategoria (opcional)
            tags: Tags opcionais
        
        Note: Account fica vazio para preenchimento manual
        """
        # Formatar data/hora
        if isinstance(date, datetime):
            time_str = date.strftime('%Y-%m-%d %H:%M:%S')
        else:
            time_str = str(date)
        
        # Valor absoluto para despesas
        amount_val = abs(float(amount))
        
        row = [
            time_str,                    # Time
            self.timezone,               # Timezone
            'Expense',                   # Type
            category,                    # Category
            subcategory,                 # Sub Category
            '',                          # Account (vazio - usuário preenche)
            self.currency,               # Account Currency
            f"{amount_val:.2f}",        # Amount
            '',                          # Account2
            '',                          # Account2 Currency
            '',                          # Account2 Amount
            '',                          # Geographic Location
            tags,                        # Tags
            description                  # Description
        ]
        
        self.writer.writerow(row)
    
    def write_income(self, date, amount: str, description: str,
                    category: str, subcategory: str = '', tags: str = ''):
        """
        Escreve uma transação de receita
        
        Args:
            date: datetime object ou string YYYY-MM-DD HH:MM:SS
            amount: Valor (positivo)
            description: Descrição da receita
            category: Categoria da receita
            subcategory: Subcategoria (opcional)
            tags: Tags opcionais
        
        Note: Account fica vazio para preenchimento manual
        """
        # Formatar data/hora
        if isinstance(date, datetime):
            time_str = date.strftime('%Y-%m-%d %H:%M:%S')
        else:
            time_str = str(date)
        
        # Valor absoluto para receitas
        amount_val = abs(float(amount))
        
        row = [
            time_str,                    # Time
            self.timezone,               # Timezone
            'Income',                    # Type
            category,                    # Category
            subcategory,                 # Sub Category
            '',                          # Account (vazio - usuário preenche)
            self.currency,               # Account Currency
            f"{amount_val:.2f}",        # Amount
            '',                          # Account2
            '',                          # Account2 Currency
            '',                          # Account2 Amount
            '',                          # Geographic Location
            tags,                        # Tags
            description                  # Description
        ]
        
        self.writer.writerow(row)
    
    def close(self):
        """Fecha o arquivo CSV"""
        if self.file:
            self.file.close()
            self.file = None
            self.writer = None
