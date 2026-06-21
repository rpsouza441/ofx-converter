#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Processor para CSV de conta digital XP."""

from pathlib import Path

from services.xp_conta_parser import XPContaParser as XPContaParserService


class XPContaProcessor:
    key = 'xp_conta'
    name = 'CSV XP Conta'

    def __init__(self, xp_conta_parser):
        self.xp_conta_parser = xp_conta_parser

    def can_handle(self, file_path: Path) -> bool:
        return file_path.suffix.lower() == '.csv' and XPContaParserService.is_xp_conta_csv(file_path)

    def parse(self, file_path: Path):
        return self.xp_conta_parser.parse_csv(file_path)
