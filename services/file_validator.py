#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File Validator Service
Responsável por validar arquivos OFX
"""

from pathlib import Path


class FileValidator:
    """Valida arquivos OFX/QFX"""
    
    def is_valid_ofx_file(self, file_path: Path) -> bool:
        """
        Verifica se é um arquivo OFX/QFX válido
        
        Args:
            file_path: Path do arquivo a validar
            
        Returns:
            True se arquivo tem extensão .ofx ou .qfx
        """
        return file_path.suffix.lower() in ['.ofx', '.qfx']
