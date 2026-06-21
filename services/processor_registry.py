#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Registry ordered by file detection priority."""

import logging
from pathlib import Path
from typing import Iterable, Optional

logger = logging.getLogger(__name__)


class ProcessorRegistry:
    """Resolve o processor correto para cada arquivo."""

    def __init__(self, processors: Iterable):
        self.processors = list(processors)
        self._by_key = {processor.key: processor for processor in self.processors}

    def find(self, file_path: Path):
        for processor in self.processors:
            try:
                if processor.can_handle(file_path):
                    logger.info(f"Processor selecionado para '{file_path.name}': {processor.name}")
                    return processor
            except Exception as e:
                logger.debug(
                    f"Processor {processor.name} falhou ao avaliar {file_path.name}: {e}"
                )

        return None

    def get(self, key: str):
        return self._by_key[key]

    def get_optional(self, key: str) -> Optional[object]:
        return self._by_key.get(key)
