#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QIF Writer Service
Responsável por escrever arquivos QIF
"""

import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class QIFWriter:
    """Escreve arquivos QIF formatados"""
    
    def __init__(self):
        self.file_handle = None
    
    def create_qif_file(self, output_path: Path):
        """
        Cria arquivo QIF e escreve cabeçalho
        
        Args:
            output_path: Caminho onde salvar o QIF
            
        Returns:
            File handle aberto para escrita
        """
        self.file_handle = open(output_path, 'w', encoding='utf-8')
        self.file_handle.write('!Type:Bank\n')
        return self.file_handle
    
    def write_transaction(self, date: str, amount: str, description: str, category: str):
        """
        Escreve uma transação no QIF
        
        Args:
            date: Data (YYYY-MM-DD)
            amount: Valor
            description: Descrição
            category: Categoria
        """
        if not self.file_handle:
            raise ValueError("QIF file not created. Call create_qif_file() first.")
        
        self.file_handle.write(f'D{date}\n')
        self.file_handle.write(f'T{amount}\n')
        self.file_handle.write(f'P{description}\n')
        self.file_handle.write(f'L{category}\n')
        self.file_handle.write('^\n')
    
    def close(self):
        """Fecha arquivo e ajusta permissões"""
        if self.file_handle:
            file_path = self.file_handle.name
            self.file_handle.close()
            self.file_handle = None
            
            # Ajustar permissões (rw-rw-r--)
            try:
                os.chmod(file_path, 0o664)
                logger.debug(f"Permissoes ajustadas: {file_path}")
            except Exception as e:
                logger.warning(f"Nao foi possivel ajustar permissoes: {e}")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
