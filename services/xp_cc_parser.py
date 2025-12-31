#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XP Credit Card CSV Parser Service
Responsável por parsear arquivos CSV de fatura de cartão de crédito do XP
"""

import csv
import re
import logging
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
                    
                    transaction = self._parse_transaction(row)
                    if transaction:
                        transactions.append(transaction)
            
            logger.info(f"Parse XP CC concluído: {len(transactions)} transações")
            return transactions if transactions else None
            
        except Exception as e:
            logger.error(f"Erro no parse CSV XP CC: {e}")
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
            # Extrair e converter data (DD/MM/YYYY -> YYYY-MM-DD)
            date_str = row['Data'].strip()
            date = self._convert_date(date_str)
            if not date:
                logger.warning(f"Data inválida: {date_str}")
                return None
            
            # Extrair estabelecimento e portador
            estabelecimento = row['Estabelecimento'].strip()
            portador = row['Portador'].strip()
            parcela_info = row['Parcela'].strip()
            
            if not estabelecimento:
                logger.warning("Estabelecimento vazio, pulando transação")
                return None
            
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
                'subcategory': cat_info['subcategory'],
                'qif_category': cat_info['qif_category']
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
    
    def _convert_date(self, date_str: str) -> Optional[str]:
        """
        Converte data de DD/MM/YYYY para YYYY-MM-DD HH:MM:SS
        
        Args:
            date_str: Data no formato DD/MM/YYYY
            
        Returns:
            Data no formato YYYY-MM-DD HH:MM:SS ou None se inválida
        """
        try:
            # Parse DD/MM/YYYY
            dt = datetime.strptime(date_str, '%d/%m/%Y')
            # Retornar YYYY-MM-DD HH:MM:SS (com horário padrão 00:00:00)
            return dt.strftime('%Y-%m-%d 00:00:00')
        except ValueError:
            return None
    
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
        Categoriza transação usando as regras do categorizer
        
        Args:
            description: Descrição da transação
            amount: Valor da transação (negativo = estorno/pagamento)
            
        Returns:
            Dict com type, category, subcategory, qif_category
        """
        description_lower = description.lower()
        
        # Se valor for negativo, é estorno ou pagamento de fatura (Income)
        if amount < 0:
            # Buscar nas regras de receita do categorizer
            for rule in self.categorizer.income_rules:
                keywords = [str(k).lower() for k in rule['keywords']]
                if any(keyword in description_lower for keyword in keywords):
                    return {
                        'type': 'income',
                        'category': rule['category'],
                        'subcategory': rule.get('subcategory', ''),
                        'qif_category': rule['category']
                    }
            
            # Fallback para estornos: Diversos > Reembolso
            return {
                'type': 'income',
                'category': 'Diversos',
                'subcategory': 'Reembolso',
                'qif_category': 'Diversos'
            }
        
        # Para valores positivos (compras), buscar nas regras de despesa
        for rule in self.categorizer.expense_rules:
            keywords = [str(k).lower() for k in rule['keywords']]
            if any(keyword in description_lower for keyword in keywords):
                return {
                    'type': 'expense',
                    'category': rule['category'],
                    'subcategory': rule.get('subcategory', ''),
                    'qif_category': rule['category']
                }
        
        # Fallback: Diversos > Outras Despesas
        return {
            'type': 'expense',
            'category': 'Diversos',
            'subcategory': 'Outras Despesas',
            'qif_category': 'Diversos'
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
