#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Text Normalizer Service
Responsável por normalização de texto e remoção de acentos
"""

import unicodedata


class TextNormalizer:
    """Normaliza texto removendo acentos e substituindo palavras problemáticas"""
    
    def __init__(self):
        # Palavras que causam interpretacao como transferencia
        self.replacements = {
            'Transferencia': 'Transacao',
            'Transfer': 'Transacao', 
            '* PROV *': 'DIV',
            'PROV': 'DIV',
            'Credito Evento B3': 'Receita B3',
            'RENDIMENTO': 'Dividendo',
            'Transferencia Recebida': 'Receita Pix',
            'Transferencia recebida': 'Receita Pix',
            'Transferencia enviada': 'Despesa Pix'
        }
    
    def normalize_utf8(self, text: str) -> str:
        """Remove acentos de um texto usando NFD"""
        if not text:
            return text
        
        # Normalizar NFD (separa caractere base de acento)
        normalized = unicodedata.normalize('NFD', text)
        
        # Remover caracteres de categoria Mn (marcas não-espacejadas = acentos)
        without_accents = ''.join(
            char for char in normalized 
            if unicodedata.category(char) != 'Mn'
        )
        
        return without_accents
    
    def clean_memo(self, memo: str) -> str:
        """Remove palavras problematicas (memo ja deve estar normalizado)"""
        if not memo:
            return memo
        
        cleaned = memo
        for old, new in self.replacements.items():
            cleaned = cleaned.replace(old, new)
        
        return cleaned
    
    def add_replacement(self, old_word: str, new_word: str):
        """Adiciona uma nova regra de substituicao"""
        self.replacements[old_word] = new_word
