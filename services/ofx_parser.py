#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OFX Parser Service
Responsável por parsear arquivos OFX e gerar transações para QIF
"""

import re
import logging
from pathlib import Path
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class OFXParser:
    """Parser de arquivos OFX com estratégias ofxparse e regex fallback"""
    
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
    
    def parse_with_ofxparse(self, ofx_file: Path) -> Optional[List[Dict]]:
        """
        Parse usando biblioteca ofxparse
        
        Args:
            ofx_file: Path do arquivo OFX
            
        Returns:
            Lista de transações ou None se falhar
        """
        try:
            import ofxparse
            
            with open(ofx_file, 'rb') as f:
                ofx = ofxparse.OfxParser.parse(f)
            
            transactions = []
            
            for account in ofx.accounts:
                for txn in account.statement.transactions:
                    date = txn.date.strftime('%Y-%m-%d %H:%M:%S')
                    amount = str(txn.amount)
                    
                    # Extrair payee e memo
                    payee = getattr(txn, 'payee', '') or ''
                    memo = getattr(txn, 'memo', '') or ''
                    
                    # Normalizar
                    if payee:
                        payee = self.text_normalizer.normalize_utf8(payee)
                    if memo:
                        memo = self.text_normalizer.normalize_utf8(memo)
                    
                    # Combinar descricao
                    if payee and memo:
                        description = f"{payee} - {memo}"
                    elif payee:
                        description = payee
                    elif memo:
                        description = memo
                    else:
                        description = ''
                    
                    # Limpar descricao
                    description = self.text_normalizer.clean_memo(description)
                    
                    # Detectar transferências e categorizar
                    cat_info = self._categorize_ofx_transaction(description, txn.amount)
                    
                    transactions.append({
                        'date': date,
                        'amount': amount,
                        'description': description,
                        'type': cat_info['type'],
                        'category': cat_info['category'],
                        'subcategory': cat_info['subcategory'],
                        'qif_category': cat_info['qif_category']
                    })
            
            logger.info(f"Parse ofxparse concluido: {len(transactions)} transacoes")
            return transactions
            
        except Exception as e:
            logger.error(f"Erro no parse com biblioteca: {e}")
            return None
    
    def parse_with_regex(self, content: str) -> Optional[List[Dict]]:
        """
        Parse usando regex (fallback)
        
        Args:
            content: Conteúdo do arquivo OFX
            
        Returns:
            Lista de transações ou None se falhar
        """
        try:
            # Encontrar transacoes
            entries = re.findall(r'<STMTTRN>(.*?)</STMTTRN>', content, re.DOTALL)
            
            if not entries:
                logger.warning("Nenhuma transacao encontrada")
                return None
            
            transactions = []
            
            for entry in entries:
                # Extrair data
                date_match = re.search(r'<DTPOSTED>(\d+)', entry)
                if not date_match:
                    continue
                
                date_str = date_match.group(1)
                formatted_date = self.date_extractor.parse_ofx_date(date_str)
                
                if not formatted_date:
                    continue
                
                # Extrair valor
                amt_match = re.search(r'<TRNAMT>([-.\\\d]+)', entry)
                amount_str = amt_match.group(1) if amt_match else '0.00'
                
                # Validar e sanitizar amount
                try:
                    # Verificar se é um valor válido (não apenas '-' ou '.')
                    if amount_str and amount_str not in ['-', '.', '-.']:
                        amount = float(amount_str)
                        amount_str = str(amount)
                    else:
                        logger.warning(f"Valor invalido encontrado: '{amount_str}', usando 0.00")
                        amount = 0.0
                        amount_str = '0.00'
                except ValueError:
                    logger.warning(f"Nao foi possivel converter '{amount_str}' para float, usando 0.00")
                    amount = 0.0
                    amount_str = '0.00'
                
                # Extrair NAME e MEMO
                name_match = re.search(r'<NAME>([^<]+)', entry)
                name = name_match.group(1).strip() if name_match else ''
                
                memo_match = re.search(r'<MEMO>([^<]+)', entry)
                memo = memo_match.group(1).strip() if memo_match else ''
                
                # Normalizar NAME e MEMO
                if name:
                    name = self.text_normalizer.normalize_utf8(name)
                if memo:
                    memo = self.text_normalizer.normalize_utf8(memo)
                
                # Combinar descricao
                if name and memo:
                    description = f"{name} - {memo}"
                elif name:
                    description = name
                elif memo:
                    description = memo
                else:
                    description = ''
                
                # Limpar descricao
                description = self.text_normalizer.clean_memo(description)
                
                # Detectar transferências e categorizar
                cat_info = self._categorize_ofx_transaction(description, amount)
                
                transactions.append({
                    'date': formatted_date,
                    'amount': amount_str,
                    'description': description,
                    'type': cat_info['type'],
                    'category': cat_info['category'],
                    'subcategory': cat_info['subcategory'],
                    'qif_category': cat_info['qif_category']
                })
            
            logger.info(f"Parse regex concluido: {len(transactions)} transacoes")
            return transactions
            
        except Exception as e:
            logger.error(f"Erro no parse regex: {e}")
            return None
    
    def _categorize_ofx_transaction(self, description: str, amount: float) -> dict:
        """
        Categoriza transação OFX usando categorize_smart do categorizer
        
        Args:
            description: Descrição da transação
            amount: Valor da transação
            
        Returns:
            Dict com type, category, subcategory, qif_category
        """
        # Usar categorize_smart que detecta tudo via YAML
        cat_info = self.categorizer.categorize_smart(description, amount)
        
        # Adicionar qif_category para compatibilidade QIF
        if cat_info['type'] == 'transfer':
            # QIF usa bracket notation para transferências
            cat_info['qif_category'] = f"[{cat_info['category']}]"
        else:
            # QIF usa categoria normal
            cat_info['qif_category'] = cat_info['category']
        
        return cat_info
