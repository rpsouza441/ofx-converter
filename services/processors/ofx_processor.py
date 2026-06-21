#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Processor para arquivos OFX/QFX."""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class OFXProcessor:
    key = 'ofx'
    name = 'OFX/QFX'

    def __init__(self, file_reader, ofx_parser):
        self.file_reader = file_reader
        self.ofx_parser = ofx_parser

    def can_handle(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in ['.ofx', '.qfx']

    def parse(self, file_path: Path):
        content = self.file_reader.read_with_encoding_detection(file_path)
        transactions = self.ofx_parser.parse_with_ofxparse(file_path)

        if not transactions:
            logger.info("Método biblioteca falhou, tentando metodo regex...")
            transactions = self.ofx_parser.parse_with_regex(content)

        return transactions

    def get_month_year(self, file_path: Path, transactions, date_extractor) -> str:
        content = self.file_reader.read_with_encoding_detection(file_path)
        return date_extractor.extract_month_year_from_ofx(content)
