#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Processor para XLSX de investimentos Rico/XP."""

from pathlib import Path


class RicoInvestimentoProcessor:
    key = 'rico_investimento'
    name = 'XLSX Rico/XP Investimento'

    def __init__(self, rico_investimento_parser):
        self.rico_investimento_parser = rico_investimento_parser

    def can_handle(self, file_path: Path) -> bool:
        if file_path.suffix.lower() != '.xlsx':
            return False

        filename_lower = file_path.stem.lower()
        has_investimento = 'investimento' in filename_lower
        has_brand = 'rico' in filename_lower or 'xp' in filename_lower
        return has_investimento and has_brand

    def parse(self, file_path: Path):
        return self.rico_investimento_parser.parse(str(file_path))
