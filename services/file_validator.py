#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File Validator Service
Responsável por validar arquivos OFX
"""

from pathlib import Path


class FileValidator:
    """Valida arquivos OFX/QFX e CSV"""
    
    def is_valid_ofx_file(self, file_path: Path) -> bool:
        """
        Verifica se é um arquivo OFX/QFX válido
        
        Args:
            file_path: Path do arquivo a validar
            
        Returns:
            True se arquivo tem extensão .ofx ou .qfx
        """
        return file_path.suffix.lower() in ['.ofx', '.qfx']
    
    def is_valid_mercadopago_csv(self, file_path: Path) -> bool:
        """
        Verifica se é um arquivo CSV válido
        
        Args:
            file_path: Path do arquivo a validar
            
        Returns:
            True se arquivo tem extensão .csv
        """
        return file_path.suffix.lower() == '.csv'
    
    def is_valid_rico_csv(self, file_path: Path) -> bool:
        """
        Verifica se é um arquivo CSV da Rico
        
        Args:
            file_path: Path do arquivo a validar
            
        Returns:
            True se arquivo CSV tem "rico" no nome (case insensitive)
        """
        if file_path.suffix.lower() != '.csv':
            return False
        
        # Detectar pela palavra "rico" no nome do arquivo
        return 'rico' in file_path.stem.lower()
    
    def is_valid_rico_investimento_xlsx(self, file_path: Path) -> bool:
        """
        Verifica se é um arquivo XLSX de investimentos da Rico
        
        Args:
            file_path: Path do arquivo a validar
            
        Returns:
            True se arquivo XLSX tem "rico" e "investimento" no nome
        """
        if file_path.suffix.lower() != '.xlsx':
            return False
        
        # Detectar por "rico" e "investimento" no nome
        filename_lower = file_path.stem.lower()
        return 'rico' in filename_lower and 'investimento' in filename_lower
    
    def is_valid_xp_cartao_csv(self, file_path: Path) -> bool:
        """
        Verifica se é um arquivo CSV de cartão de crédito da XP
        
        Args:
            file_path: Path do arquivo a validar
            
        Returns:
            True se arquivo CSV tem header XP
        """
        from services.xp_cartao_parser import XPCartaoParser
        
        if file_path.suffix.lower() != '.csv':
            return False
        
        return XPCartaoParser.is_xp_cartao_csv(file_path)
