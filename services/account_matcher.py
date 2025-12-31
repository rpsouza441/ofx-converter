#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Account Matcher Service
Responsável por identificar a conta baseada no nome do arquivo
"""

import logging
from pathlib import Path
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)


class AccountMatcher:
    """Identifica conta do ezBookkeeping baseado em palavras-chave no nome do arquivo"""
    
    def __init__(self, config_file: str = None):
        """
        Inicializa o matcher com arquivo de configuração
        
        Args:
            config_file: Caminho para arquivo YAML de configuração de contas
        """
        self.accounts: List[Dict] = []
        
        if config_file and Path(config_file).exists():
            self.load_config(config_file)
    
    def load_config(self, file_path: str):
        """
        Carrega configuração de contas do arquivo YAML
        
        Args:
            file_path: Caminho para arquivo YAML
        """
        try:
            import yaml
            
            with open(file_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # Carregar todas as categorias de contas
            for categoria in ['contas_correntes', 'cartoes_credito', 'contas_virtuais', 'contas_investimento']:
                if categoria in config:
                    for account in config[categoria]:
                        self.accounts.append({
                            'conta': account['conta'],
                            'titular': [t.lower() for t in account.get('titular', [])],
                            'banco': [b.lower() for b in account.get('banco', [])],
                            'tipo': [t.lower() for t in account.get('tipo', [])],
                            'prioridade': account.get('prioridade', 0)
                        })
            
            logger.info(f"Carregadas {len(self.accounts)} contas de: {file_path}")
            
        except ImportError:
            logger.warning("PyYAML não instalado, account matching desabilitado")
        except Exception as e:
            logger.error(f"Erro ao carregar configuração de contas: {e}")
    
    def match_account(self, filename: str) -> Optional[str]:
        """
        Identifica conta baseada no nome do arquivo
        
        Args:
            filename: Nome do arquivo (com ou sem path)
            
        Returns:
            Nome da conta ou None se não encontrar match
        """
        if not self.accounts:
            logger.debug("Nenhuma conta configurada para matching")
            return None
        
        # Extrair apenas o nome do arquivo (sem path e extensão)
        filename_clean = Path(filename).stem.lower()
        
        # Substituir separadores por espaços para facilitar matching
        filename_normalized = filename_clean.replace('_', ' ').replace('-', ' ').replace('.', ' ')
        
        logger.debug(f"Matching arquivo: '{filename}' -> '{filename_normalized}'")
        
        matches = []
        
        for account in self.accounts:
            # Verificar se encontra pelo menos uma palavra-chave de cada categoria presente
            titular_match = self._has_keyword_match(filename_normalized, account['titular'])
            banco_match = self._has_keyword_match(filename_normalized, account['banco'])
            tipo_match = self._has_keyword_match(filename_normalized, account['tipo'])
            
            # Score: quantas categorias tiveram match
            score = sum([titular_match, banco_match, tipo_match])
            
            # Só considera se tiver match em pelo menos 2 categorias (banco + titular ou banco + tipo)
            if score >= 2:
                matches.append({
                    'conta': account['conta'],
                    'score': score,
                    'prioridade': account['prioridade'],
                    'titular_match': titular_match,
                    'banco_match': banco_match,
                    'tipo_match': tipo_match
                })
                logger.debug(f"  Match encontrado: {account['conta']} (score={score}, prio={account['prioridade']})")
        
        if not matches:
            logger.warning(f"Nenhuma conta encontrada para arquivo: {filename}")
            logger.info(f"  Palavras no arquivo: {filename_normalized}")
            return None
        
        # Ordenar por score (maior primeiro), depois por prioridade (maior primeiro)
        matches.sort(key=lambda x: (x['score'], x['prioridade']), reverse=True)
        
        best_match = matches[0]
        logger.info(f"Conta selecionada para '{filename}': {best_match['conta']}")
        
        return best_match['conta']
    
    def _has_keyword_match(self, text: str, keywords: List[str]) -> bool:
        """
        Verifica se alguma palavra-chave está presente no texto
        
        Args:
            text: Texto para buscar (já em lowercase)
            keywords: Lista de palavras-chave (já em lowercase)
            
        Returns:
            True se encontrou pelo menos uma palavra-chave
        """
        for keyword in keywords:
            if keyword in text:
                return True
        return False
    
    def add_account(self, conta: str, titular: List[str], banco: List[str], 
                   tipo: List[str], prioridade: int = 0):
        """
        Adiciona conta programaticamente
        
        Args:
            conta: Nome da conta no ezBookkeeping
            titular: Lista de palavras-chave do titular
            banco: Lista de palavras-chave do banco
            tipo: Lista de palavras-chave do tipo
            prioridade: Prioridade para desempate
        """
        self.accounts.append({
            'conta': conta,
            'titular': [t.lower() for t in titular],
            'banco': [b.lower() for b in banco],
            'tipo': [t.lower() for t in tipo],
            'prioridade': prioridade
        })
        logger.info(f"Conta adicionada: {conta}")
