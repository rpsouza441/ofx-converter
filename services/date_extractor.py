#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Date Extractor Service
Responsável por extrair mês-ano de arquivos OFX
"""

import re
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class DateExtractor:
    """Extrai datas de arquivos OFX e nomes de arquivo"""
    
    def extract_month_year_from_ofx(self, content: str) -> str:
        """
        Extrai mes-ano usando data MAIS FREQUENTE (ignora Saldo)
        
        Args:
            content: Conteúdo do arquivo OFX
            
        Returns:
            String no formato 'MM-YYYY'
        """
        try:
            # Procurar por todas as transacoes STMTTRN
            transactions = re.findall(r'<STMTTRN>(.*?)</STMTTRN>', content, re.DOTALL)
            
            month_year_counts = {}
            
            for trn in transactions:
                # Pular transacoes de "Saldo" (Saldo Anterior, Saldo do dia)
                if re.search(r'<NAME>Saldo', trn, re.IGNORECASE):
                    continue
                
                # Extrair data desta transacao
                date_match = re.search(r'<DTPOSTED>(\d{8})', trn)
                if date_match:
                    date_str = date_match.group(1)
                    try:
                        date_obj = datetime.strptime(date_str, '%Y%m%d')
                        month_year = date_obj.strftime('%m-%Y')
                        month_year_counts[month_year] = month_year_counts.get(month_year, 0) + 1
                    except:
                        continue
            
            # Usar o mes-ano mais frequente
            if month_year_counts:
                most_common = max(month_year_counts.items(), key=lambda x: x[1])
                return most_common[0]

            # Fallback: DTSTART/DTEND
            start_match = re.search(r'<DTSTART>(\d{8})', content)
            if start_match:
                date_obj = datetime.strptime(start_match.group(1), '%Y%m%d')
                return date_obj.strftime('%m-%Y')

            # Ultimo fallback: data atual
            return datetime.now().strftime('%m-%Y')

        except Exception as e:
            logger.warning(f"Erro ao extrair data do OFX: {e}")
            return datetime.now().strftime('%m-%Y')
    
    def extract_from_filename(self, filename: str) -> str:
        """
        Extrai mes-ano do nome do arquivo
        
        Formatos suportados:
        - extrato-112025.ofx -> 11-2025
        - extrato-11-2025.ofx -> 11-2025
        - extrato-novembro-2025.ofx -> 11-2025
        """
        try:
            # Padrão: 112025 ou 11-2025
            match = re.search(r'(\d{1,2})[-_]?(\d{4})', filename)
            if match:
                month = match.group(1).zfill(2)
                year = match.group(2)
                return f"{month}-{year}"
            
            # Fallback: mes atual
            return datetime.now().strftime('%m-%Y')
            
        except Exception as e:
            logger.warning(f"Erro ao extrair data do nome: {e}")
            return datetime.now().strftime('%m-%Y')
    
    def parse_ofx_date(self, date_str: str) -> str:
        """
        Parse data do OFX (YYYYMMDD) para formato YYYY-MM-DD
        
        Args:
            date_str: Data em formato OFX (ex: 20251108)
            
        Returns:
            Data formatada YYYY-MM-DD ou string vazia se inválida
        """
        try:
            if len(date_str) >= 8:
                year = int(date_str[0:4])
                month = int(date_str[4:6])
                day = int(date_str[6:8])
                
                # Corrigir ano invalido
                if year < 1900:
                    year = datetime.now().year
                
                # Validar mes e dia
                if month > 12:
                    month = 12
                if day > 31 or day == 0:
                    day = 1
                
                date_obj = datetime(year, month, day)
                return date_obj.strftime('%Y-%m-%d')
            
            return ''
        except Exception as e:
            logger.warning(f"Erro ao parsear data '{date_str}': {e}")
            return ''

