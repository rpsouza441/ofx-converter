#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OFX File Reader Service
Responsável por ler arquivos OFX com detecção automática de encoding
"""

import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)


class OFXFileReader:
    """Lê arquivos OFX tentando múltiplos encodings"""
    
    def __init__(self):
        self.encodings = ['utf-8', 'latin-1', 'cp1252']
        # Mapeamento de CHARSET OFX para encoding Python
        self.charset_map = {
            '1252': 'cp1252',
            'ANSI': 'cp1252',
            'ISO-8859-1': 'latin-1',
            '8859-1': 'latin-1',
            'NONE': 'utf-8',
            'UTF-8': 'utf-8',
        }
    
    def read_with_encoding_detection(self, file_path: Path) -> str:
        """
        Lê arquivo OFX tentando detectar encoding automaticamente
        
        Args:
            file_path: Path do arquivo OFX
            
        Returns:
            Conteúdo do arquivo como string
        """
        # Primeiro, ler o cabeçalho em modo binário para detectar encoding declarado
        declared_encoding = self._detect_encoding_from_header(file_path)
        
        if declared_encoding:
            content = self._try_encoding(file_path, declared_encoding)
            if content:
                logger.debug(f"Arquivo lido com encoding declarado: {declared_encoding}")
                return content
        
        # Tentar UTF-8 primeiro (padrão declarado em muitos OFX)
        content = self._try_encoding(file_path, 'utf-8')
        if content:
            logger.debug(f"Arquivo lido com encoding: UTF-8")
            return content
        
        # Tentar latin-1 (comum em bancos brasileiros)
        content = self._try_encoding(file_path, 'latin-1')
        if content:
            logger.debug(f"Arquivo lido com encoding: latin-1 (fallback)")
            return content
        
        # Último recurso: cp1252 (Windows)
        content = self._try_encoding(file_path, 'cp1252')
        if content:
            logger.debug(f"Arquivo lido com encoding: cp1252 (fallback)")
            return content
        
        # Fallback final: latin-1 com replace
        logger.warning(f"Nao foi possivel detectar encoding, usando latin-1 com replace")
        with open(file_path, 'r', encoding='latin-1', errors='replace') as f:
            return f.read()
    
    def _detect_encoding_from_header(self, file_path: Path) -> str:
        """
        Detecta encoding a partir do cabeçalho OFX
        
        Args:
            file_path: Path do arquivo OFX
            
        Returns:
            Encoding detectado ou None
        """
        try:
            # Ler primeiros bytes em modo binário para analisar cabeçalho
            with open(file_path, 'rb') as f:
                header = f.read(500).decode('ascii', errors='ignore')
            
            # Procurar CHARSET no cabeçalho
            charset_match = re.search(r'CHARSET[:\s]*(\S+)', header, re.IGNORECASE)
            if charset_match:
                charset = charset_match.group(1).upper()
                if charset in self.charset_map:
                    logger.debug(f"CHARSET declarado no OFX: {charset} -> {self.charset_map[charset]}")
                    return self.charset_map[charset]
            
            # Procurar ENCODING no cabeçalho
            encoding_match = re.search(r'ENCODING[:\s]*(\S+)', header, re.IGNORECASE)
            if encoding_match:
                encoding = encoding_match.group(1).upper()
                if encoding == 'UTF-8':
                    return 'utf-8'
                elif encoding == 'USASCII' or encoding == 'ASCII':
                    # USASCII geralmente significa que CHARSET define o encoding real
                    charset_match = re.search(r'CHARSET[:\s]*(\S+)', header, re.IGNORECASE)
                    if charset_match:
                        charset = charset_match.group(1).upper()
                        if charset in self.charset_map:
                            return self.charset_map[charset]
                    return 'cp1252'  # Default para arquivos brasileiros
            
            return None
            
        except Exception as e:
            logger.debug(f"Erro ao detectar encoding do cabeçalho: {e}")
            return None
    
    def _try_encoding(self, file_path: Path, encoding: str) -> str:
        """Tenta ler arquivo com encoding específico"""
        try:
            with open(file_path, 'r', encoding=encoding, errors='strict') as f:
                return f.read()
        except UnicodeDecodeError:
            return None
