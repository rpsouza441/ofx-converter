#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OFX File Reader Service
Responsável por ler arquivos OFX com detecção automática de encoding
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class OFXFileReader:
    """Lê arquivos OFX tentando múltiplos encodings"""
    
    def __init__(self):
        self.encodings = ['utf-8', 'latin-1', 'cp1252']
    
    def read_with_encoding_detection(self, file_path: Path) -> str:
        """
        Lê arquivo OFX tentando detectar encoding automaticamente
        
        Args:
            file_path: Path do arquivo OFX
            
        Returns:
            Conteúdo do arquivo como string
        """
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
    
    def _try_encoding(self, file_path: Path, encoding: str) -> str:
        """Tenta ler arquivo com encoding específico"""
        try:
            with open(file_path, 'r', encoding=encoding, errors='strict') as f:
                return f.read()
        except UnicodeDecodeError:
            return None
