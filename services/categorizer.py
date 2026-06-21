#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Transaction Categorizer Service
Responsável por categorizar transações baseado em regras
"""

import logging
import re
from pathlib import Path
from typing import Dict, List, Optional

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

    def _keyword_matches(self, description_lower: str, keyword: str) -> bool:
        """
        Verifica se a palavra-chave bate com a descrição.

        Para termos textuais, usa limite de palavra para evitar falsos positivos
        como "game" dentro de "pagamento". Para padrões com símbolos, mantém
        busca por substring para não quebrar regras existentes.
        """
        if not keyword:
            return False

        if re.fullmatch(r"[\w\s]+", keyword, flags=re.UNICODE):
            pattern = r"\b" + re.escape(keyword) + r"\b"
            return re.search(pattern, description_lower, flags=re.UNICODE) is not None

        return keyword in description_lower

    def _composite_keyword_matches(self, description_lower: str, keywords: List[str]) -> bool:
        """Verifica uma regra composta que exige todos os termos."""
        return all(self._keyword_matches(description_lower, keyword) for keyword in keywords)

    def _find_best_rule_match(self, description_lower: str, rules: List[Dict]) -> Optional[Dict]:
        """
        Retorna a regra com match mais específico.

        Prioridade:
        1. Palavra-chave mais longa
        2. Regra com menor número de palavras-chave
        3. Ordem original de carregamento
        """
        best_rule = None
        best_keyword = None

        for rule in rules:
            matched_keywords = [
                keyword for keyword in rule['keywords']
                if self._keyword_matches(description_lower, keyword)
            ]

            for keywords in rule.get('all_keywords', []):
                if self._composite_keyword_matches(description_lower, keywords):
                    matched_keywords.append(' '.join(keywords))

            if not matched_keywords:
                continue

            rule_best_keyword = max(matched_keywords, key=len)

            if best_rule is None:
                best_rule = rule
                best_keyword = rule_best_keyword
                continue

            if len(rule_best_keyword) > len(best_keyword):
                best_rule = rule
                best_keyword = rule_best_keyword
                continue

            if len(rule_best_keyword) == len(best_keyword):
                current_keywords_count = len(rule.get('keywords', []))
                best_keywords_count = len(best_rule.get('keywords', []))
                if current_keywords_count < best_keywords_count:
                    best_rule = rule
                    best_keyword = rule_best_keyword

        return best_rule
    
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
        transfer_rule = self._find_best_rule_match(description_lower, self.transfer_rules)
        if transfer_rule:
            logger.info(f"MATCHED TRANSFER: {description} -> {transfer_rule['category']}")
            return {
                'type': 'transfer',
                'category': transfer_rule['category'],
                'subcategory': transfer_rule['subcategory']
            }
        
        # 2. Se não for transferência, categoriza como receita/despesa
        if amount > 0:
            income_rule = self._find_best_rule_match(description_lower, self.income_rules)
            if income_rule:
                return {
                    'type': 'income',
                    'category': income_rule['category'],
                    'subcategory': income_rule.get('subcategory', '')
                }
            # Fallback
            return {
                'type': 'income',
                'category': 'Diversos',
                'subcategory': 'Outras Receitas'
            }
        else:
            expense_rule = self._find_best_rule_match(description_lower, self.expense_rules)
            if expense_rule:
                return {
                    'type': 'expense',
                    'category': expense_rule['category'],
                    'subcategory': expense_rule.get('subcategory', '')
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
                    keywords = [k.lower() for k in rule.get('palavras', [])]
                    self.add_income_rule(category, subcategory, keywords)
                    self.income_rules[-1]['all_keywords'] = [
                        [k.lower() for k in keywords]
                        for keywords in rule.get('todas_palavras', [])
                    ]
            
            # Carregar despesas
            if 'despesas' in rules:
                for rule in rules['despesas']:
                    category = rule['categoria']
                    subcategory = rule.get('subcategoria', '')
                    keywords = [k.lower() for k in rule.get('palavras', [])]
                    self.add_expense_rule(category, subcategory, keywords)
                    self.expense_rules[-1]['all_keywords'] = [
                        [k.lower() for k in keywords]
                        for keywords in rule.get('todas_palavras', [])
                    ]
            
            # Carregar transferências
            if 'transferencias' in rules:
                for rule in rules['transferencias']:
                    category = rule['categoria']
                    subcategory = rule.get('subcategoria', '')
                    keywords = [k.lower() for k in rule.get('palavras', [])]
                    self.add_transfer_rule(category, subcategory, keywords)
                    self.transfer_rules[-1]['all_keywords'] = [
                        [k.lower() for k in keywords]
                        for keywords in rule.get('todas_palavras', [])
                    ]
            
            logger.info(f"Regras carregadas de: {file_path}")
            
        except ImportError:
            logger.warning("PyYAML nao instalado, usando regras padrao")
        except Exception as e:
            logger.error(f"Erro ao carregar regras: {e}")
