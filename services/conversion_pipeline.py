#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Common conversion pipeline.

Centralizes parse -> postprocess -> write CSV -> move input flow.
"""

import logging
import shutil
from pathlib import Path
from typing import Callable, Optional

from services.ezbookkeeping_csv_writer import EZBookkeepingCSVWriter

logger = logging.getLogger(__name__)


class ConversionPipeline:
    """Executa o fluxo comum de conversão para qualquer processor."""

    def __init__(
        self,
        lido_dir: Path,
        convertido_dir: Path,
        date_extractor,
        account_matcher,
        postprocessor,
        ownership_callback: Optional[Callable[[Path], None]] = None,
        writer_factory=EZBookkeepingCSVWriter,
    ):
        self.lido_dir = lido_dir
        self.convertido_dir = convertido_dir
        self.date_extractor = date_extractor
        self.account_matcher = account_matcher
        self.postprocessor = postprocessor
        self.ownership_callback = ownership_callback
        self.writer_factory = writer_factory

    def convert(self, file_path: Path, processor, validate: bool = True) -> bool:
        """
        Converte um arquivo usando o processor informado.

        Args:
            file_path: arquivo de entrada.
            processor: adapter com can_handle/parse.
            validate: quando True, valida processor.can_handle antes do parse.
        """
        try:
            if validate and not processor.can_handle(file_path):
                logger.warning(f"Arquivo não é compatível com {processor.name}: {file_path.name}")
                return False

            logger.info(f"Convertendo {processor.name}: {file_path.name}")
            transactions = processor.parse(file_path)

            if not transactions:
                logger.error(f"Falha ao parsear {processor.name}: {file_path.name}")
                return False

            month_year = self._extract_month_year(file_path, processor, transactions)
            lido_month_folder = self._create_month_folder(self.lido_dir, month_year)
            convertido_month_folder = self._create_month_folder(self.convertido_dir, month_year)

            csv_path = convertido_month_folder / f'{file_path.stem}.csv'
            account_name = self.account_matcher.match_account(file_path.name) or ''
            transactions = self.postprocessor.process(transactions, account_name)

            self._write_csv(csv_path, transactions, account_name)
            logger.info(f"CSV ezBookkeeping salvo em: {csv_path}")
            self._apply_ownership(csv_path)

            lido_path = lido_month_folder / file_path.name
            shutil.move(str(file_path), str(lido_path))
            self._apply_ownership(lido_path)

            logger.info(f"Conversao bem-sucedida: {file_path.name}")
            logger.info(f"Arquivo original movido para: {lido_path}")
            logger.info(f"Organizados na pasta: {month_year}")
            return True

        except Exception as e:
            logger.error(f"Erro ao converter {file_path.name}: {e}")
            return False

    def _extract_month_year(self, file_path: Path, processor, transactions) -> str:
        if hasattr(processor, 'get_month_year'):
            return processor.get_month_year(file_path, transactions, self.date_extractor)

        return self.date_extractor.extract_month_year_from_transactions(
            [txn['date'] for txn in transactions]
        )

    def _create_month_folder(self, base_dir: Path, month_year: str) -> Path:
        month_folder = base_dir / month_year
        month_folder.mkdir(exist_ok=True)
        return month_folder

    def _write_csv(self, csv_path: Path, transactions, account_name: str):
        csv_writer = self.writer_factory()

        try:
            csv_writer.create_csv_file(csv_path)

            for txn in transactions:
                if txn['type'] == 'transfer':
                    csv_writer.write_transfer(
                        txn['date'],
                        txn['amount'],
                        txn['description'],
                        txn['category'],
                        txn['subcategory'],
                        account_name
                    )
                elif txn['type'] == 'expense':
                    csv_writer.write_expense(
                        txn['date'],
                        txn['amount'],
                        txn['description'],
                        txn['category'],
                        txn['subcategory'],
                        account_name
                    )
                elif txn['type'] == 'income':
                    csv_writer.write_income(
                        txn['date'],
                        txn['amount'],
                        txn['description'],
                        txn['category'],
                        txn['subcategory'],
                        account_name
                    )
        finally:
            csv_writer.close()

    def _apply_ownership(self, file_path: Path):
        if self.ownership_callback:
            self.ownership_callback(file_path)
