#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Services Package
Exporta todos os services para facilitar imports
"""

from services.file_reader import OFXFileReader
from services.date_extractor import DateExtractor
from services.text_normalizer import TextNormalizer
from services.categorizer import TransactionCategorizer
from services.qif_writer import QIFWriter
from services.ofx_parser import OFXParser
from services.file_validator import FileValidator
from services.mercadopago_parser import MercadoPagoParser
from services.ezbookkeeping_csv_writer import EZBookkeepingCSVWriter
from services.rico_parser import RicoParser
from services.rico_investimento_parser import RicoInvestimentoParser
from services.xp_cc_parser import XPCCParser
from services.xp_conta_parser import XPContaParser
from services.account_matcher import AccountMatcher


__all__ = [
    'OFXFileReader',
    'DateExtractor',
    'TextNormalizer',
    'TransactionCategorizer',
    'QIFWriter',
    'OFXParser',
    'FileValidator',
    'MercadoPagoParser',
    'EZBookkeepingCSVWriter',
    'RicoParser',
    'RicoInvestimentoParser',
    'XPCCParser',
    'XPContaParser',
    'AccountMatcher'
]

__version__ = '3.0.0'

