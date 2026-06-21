#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Processor para CSV da Rico."""

from pathlib import Path


class RicoProcessor:
    key = 'rico'
    name = 'CSV Rico'

    def __init__(self, rico_parser):
        self.rico_parser = rico_parser

    def can_handle(self, file_path: Path) -> bool:
        return file_path.suffix.lower() == '.csv' and 'rico' in file_path.stem.lower()

    def parse(self, file_path: Path):
        return self.rico_parser.parse(str(file_path))
