#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Processor para CSV de fatura XP CC."""

from pathlib import Path

from services.xp_cc_parser import XPCCParser as XPCCParserService


class XPCCProcessor:
    key = 'xp_cc'
    name = 'CSV XP CC'

    def __init__(self, xp_cc_parser):
        self.xp_cc_parser = xp_cc_parser

    def can_handle(self, file_path: Path) -> bool:
        return file_path.suffix.lower() == '.csv' and XPCCParserService.is_xp_cc_csv(file_path)

    def parse(self, file_path: Path):
        return self.xp_cc_parser.parse_csv(file_path)
