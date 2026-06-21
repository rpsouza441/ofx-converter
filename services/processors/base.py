#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Base processor protocol."""

from pathlib import Path
from typing import Protocol, List, Dict


class FileProcessor(Protocol):
    """Detecta e parseia um tipo de arquivo financeiro."""

    key: str
    name: str

    def can_handle(self, file_path: Path) -> bool:
        ...

    def parse(self, file_path: Path) -> List[Dict]:
        ...
