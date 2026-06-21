#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Processor para CSV do Banco do Brasil."""

from pathlib import Path

from services.bb_parser import BBParser as BBParserService


class BBProcessor:
    key = 'bb'
    name = 'CSV Banco do Brasil'

    def __init__(self, bb_parser):
        self.bb_parser = bb_parser

    def can_handle(self, file_path: Path) -> bool:
        return file_path.suffix.lower() == '.csv' and BBParserService.is_bb_csv(file_path)

    def parse(self, file_path: Path):
        return self.bb_parser.parse(str(file_path))
