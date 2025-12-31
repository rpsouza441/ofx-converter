#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Transaction Categorizer Service
Responsável por categorizar transações baseado em regras
"""

import logging
from pathlib import Path
from typing import Dict, List

logger = logging.getLogger(__name__)


class TransactionCategorizer:
    """Categoriza transações baseado em palavras-chave"""
    
    def __init__(self, rules_file: str = None):
        """
        Inicializa categorizador
        
        Args:
            rules_file: Caminho para arquivo de regras (YAML/dict)
        """
        self.income_rules = []  # Lista de dicts com {keywords, category, subcategory}
        self.expense_rules = []  # Lista de dicts com {keywords, category, subcategory}
        self.transfer_rules = []  # Lista de dicts com {keywords, category, subcategory}
        
        if rules_file and Path(rules_file).exists():
            self.load_rules_from_file(rules_file)
    
    # Regras padrão removidas - tudo vem do YAML agora
    
    def categorize_smart(self, description: str, amount: float) -> dict:
        """
        Categoriza transação automaticamente (transferência, receita ou despesa)
        
        Args:
            description: Descrição da transação (já normalizada)
            amount: Valor (positivo = entrada, negativo = saída)
            
        Returns:
            Dict com type, category, subcategory:
            {
                'type': 'transfer' | 'income' | 'expense',
                'category': str,
                'subcategory': str
            }
        """
        description_lower = description.lower()
        
        # DEBUG: Log transfer rules
        logger.debug(f"categorize_smart: description='{description}', amount={amount}")
        logger.debug(f"categorize_smart: transfer_rules count={len(self.transfer_rules)}")
        
        # 1. Primeiro verifica se é transferência (via YAML transferencias)
        for rule in self.transfer_rules:
            logger.debug(f"Checking transfer rule: {rule['category']} - keywords: {rule['keywords']}")
            if any(keyword in description_lower for keyword in rule['keywords']):
                logger.info(f"MATCHED TRANSFER: {description} -> {rule['category']}")
                return {
                    'type': 'transfer',
                    'category': rule['category'],
                    'subcategory': rule['subcategory']
                }
        
        # 2. Se não for transferência, categoriza como receita/despesa
        if amount > 0:
            for rule in self.income_rules:
                if any(keyword in description_lower for keyword in rule['keywords']):
                    return {
                        'type': 'income',
                        'category': rule['category'],
                        'subcategory': rule.get('subcategory', '')
                    }
            # Fallback
            return {
                'type': 'income',
                'category': 'Diversos',
                'subcategory': 'Outras Receitas'
            }
        else:
            for rule in self.expense_rules:
                if any(keyword in description_lower for keyword in rule['keywords']):
                    return {
                        'type': 'expense',
                        'category': rule['category'],
                        'subcategory': rule.get('subcategory', '')
                    }
            # Fallback
            return {
                'type': 'expense',
                'category': 'Diversos',
                'subcategory': 'Outras Despesas'
            }
    
    def _deprecated_categorize(self, description: str, amount: float, trn_type: str = None) -> str:
        """
        DEPRECATED: Use categorize_smart() instead
        """
        raise DeprecationWarning("Use categorize_smart() instead of categorize()")
    
    def add_income_rule(self, category: str, subcategory: str, keywords: List[str]):
        """Adiciona regra de receita"""
        self.income_rules.append({
            'category': category,
            'subcategory': subcategory,
            'keywords': keywords
        })
        logger.info(f"Regra de receita adicionada: {category} > {subcategory}")
    
    def _deprecated_add_income_rule_old(self, category: str, keywords: List[str]):
        """DEPRECATED"""
        if category in {}:
            pass
    
    def add_expense_rule(self, category: str, subcategory: str, keywords: List[str]):
        """Adiciona regra de despesa"""
        self.expense_rules.append({
            'category': category,
            'subcategory': subcategory,
            'keywords': keywords
        })
        logger.info(f"Regra de despesa adicionada: {category} > {subcategory}")
    
    def _deprecated_add_expense_rule_old(self, category: str, keywords: List[str]):
        """DEPRECATED"""
        pass
    
    def add_transfer_rule(self, category: str, subcategory: str, keywords: List[str]):
        """Adiciona regra de transferência"""
        self.transfer_rules.append({
            'category': category,
            'subcategory': subcategory,
            'keywords': keywords
        })
        logger.info(f"Regra de transferência adicionada: {category} > {subcategory}")
    
    def _deprecated_categorize_transfer(self, description: str) -> tuple:
        """
        DEPRECATED: Use categorize_smart() instead
        """
        raise DeprecationWarning("Use categorize_smart() instead of categorize_transfer()")
    
    def load_rules_from_file(self, file_path: str):
        """
        Carrega regras de arquivo YAML
        
        Formato esperado:
        receitas:
          - categoria: Salário
            palavras: [salario, ord empregador]
        despesas:
          - categoria: Boletos
            palavras: [boleto]
        """
        try:
            import yaml
            
            with open(file_path, 'r', encoding='utf-8') as f:
                rules = yaml.safe_load(f)
            
            # Carregar receitas
            if 'receitas' in rules:
                for rule in rules['receitas']:
                    category = rule['categoria']
                    subcategory = rule.get('subcategoria', '')
                    keywords = [k.lower() for k in rule['palavras']]
                    self.add_income_rule(category, subcategory, keywords)
            
            # Carregar despesas
            if 'despesas' in rules:
                for rule in rules['despesas']:
                    category = rule['categoria']
                    subcategory = rule.get('subcategoria', '')
                    keywords = [k.lower() for k in rule['palavras']]
                    self.add_expense_rule(category, subcategory, keywords)
            
            # Carregar transferências
            if 'transferencias' in rules:
                for rule in rules['transferencias']:
                    category = rule['categoria']
                    subcategory = rule.get('subcategoria', '')
                    keywords = [k.lower() for k in rule['palavras']]
                    self.add_transfer_rule(category, subcategory, keywords)
            
            logger.info(f"Regras carregadas de: {file_path}")
            
        except ImportError:
            logger.warning("PyYAML nao instalado, usando regras padrao")
        except Exception as e:
            logger.error(f"Erro ao carregar regras: {e}")
