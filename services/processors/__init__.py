#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""File processors for supported bank export formats."""

from services.processors.base import FileProcessor
from services.processors.ofx_processor import OFXProcessor
from services.processors.mercadopago_processor import MercadoPagoProcessor
from services.processors.rico_processor import RicoProcessor
from services.processors.rico_investimento_processor import RicoInvestimentoProcessor
from services.processors.xp_cc_processor import XPCCProcessor
from services.processors.xp_conta_processor import XPContaProcessor
from services.processors.bb_processor import BBProcessor

__all__ = [
    'FileProcessor',
    'OFXProcessor',
    'MercadoPagoProcessor',
    'RicoProcessor',
    'RicoInvestimentoProcessor',
    'XPCCProcessor',
    'XPContaProcessor',
    'BBProcessor',
]
