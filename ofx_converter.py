#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OFX to ezBookkeeping CSV Converter
Conversor modular com pipeline e processors por formato.
"""

import logging
import os
import time
from pathlib import Path

from services import (
    AccountMatcher,
    BBParser,
    ConversionPipeline,
    DateExtractor,
    FileValidator,
    MercadoPagoParser,
    OFXFileReader,
    OFXParser,
    ProcessorRegistry,
    RicoInvestimentoParser,
    RicoParser,
    TextNormalizer,
    TransactionCategorizer,
    TransactionPostProcessor,
    XPCCParser,
    XPContaParser,
)
from services.processors import (
    BBProcessor,
    MercadoPagoProcessor,
    OFXProcessor,
    RicoInvestimentoProcessor,
    RicoProcessor,
    XPCCProcessor,
    XPContaProcessor,
)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/converter.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class OFXConverter:
    """Conversor de arquivos financeiros para CSV do ezBookkeeping."""

    def __init__(self):
        self.entrada_dir = Path('/app/entrada')
        self.lido_dir = Path('/app/entrada/lido')
        self.convertido_dir = Path('/app/convertido')
        self.logs_dir = Path('/app/logs')

        for directory in [self.lido_dir, self.convertido_dir, self.logs_dir]:
            directory.mkdir(parents=True, exist_ok=True)

        self.file_reader = OFXFileReader()
        self.date_extractor = DateExtractor()
        self.text_normalizer = TextNormalizer()
        self.file_validator = FileValidator()

        categorias_file = Path('/app/categorias.yaml')
        self.categorizer = TransactionCategorizer(
            rules_file=str(categorias_file) if categorias_file.exists() else None
        )

        self.ofx_parser = OFXParser(
            self.text_normalizer,
            self.categorizer,
            self.date_extractor
        )
        self.mercadopago_parser = MercadoPagoParser(
            self.text_normalizer,
            self.categorizer,
            self.date_extractor
        )
        self.rico_parser = RicoParser(self.categorizer)
        self.rico_investimento_parser = RicoInvestimentoParser(self.categorizer)
        self.xp_cc_parser = XPCCParser(
            self.text_normalizer,
            self.categorizer,
            self.date_extractor
        )
        self.xp_conta_parser = XPContaParser(
            self.text_normalizer,
            self.categorizer,
            self.date_extractor
        )
        self.bb_parser = BBParser(self.categorizer)

        contas_file = Path('/app/contas.yaml')
        self.account_matcher = AccountMatcher(
            config_file=str(contas_file) if contas_file.exists() else None
        )
        self.postprocessor = TransactionPostProcessor()
        self.registry = ProcessorRegistry(self._build_processors())
        self.pipeline = ConversionPipeline(
            lido_dir=self.lido_dir,
            convertido_dir=self.convertido_dir,
            date_extractor=self.date_extractor,
            account_matcher=self.account_matcher,
            postprocessor=self.postprocessor,
            ownership_callback=self._apply_file_ownership,
        )

        logger.info("OFX Converter v5.0 iniciado")
        logger.info(f"Monitorando pasta: {self.entrada_dir}")
        logger.info(f"Arquivos lidos organizados por mes em: {self.lido_dir}")
        logger.info(f"Arquivos convertidos organizados por mes em: {self.convertido_dir}")
        logger.info("Formatos suportados: OFX/QFX, Mercado Pago CSV, Rico CSV/XLSX, XP CC/Conta CSV")
        logger.info("Categorizacao automatica alinhada com ezBookkeeping")

    def _build_processors(self):
        """
        Ordem importa para CSVs: detectores por header vêm antes de fallback por nome.
        """
        return [
            XPCCProcessor(self.xp_cc_parser),
            XPContaProcessor(self.xp_conta_parser),
            BBProcessor(self.bb_parser),
            RicoProcessor(self.rico_parser),
            MercadoPagoProcessor(self.mercadopago_parser),
            OFXProcessor(self.file_reader, self.ofx_parser),
            RicoInvestimentoProcessor(self.rico_investimento_parser),
        ]

    def _apply_file_ownership(self, file_path: Path):
        """
        Aplica chown opcional aos arquivos gerados/movidos.

        Controlado por variáveis de ambiente:
        - FILE_CHOWN_ENABLED=true|false
        - FILE_CHOWN_UID=1000
        - FILE_CHOWN_GID=1000
        """
        enabled = os.environ.get('FILE_CHOWN_ENABLED', 'false').lower() == 'true'
        if not enabled:
            return

        uid = int(os.environ.get('FILE_CHOWN_UID', '1000'))
        gid = int(os.environ.get('FILE_CHOWN_GID', '1000'))

        try:
            os.chown(file_path, uid, gid)
            logger.debug(f"Ownership ajustado para {uid}:{gid} em {file_path}")
        except Exception as e:
            logger.warning(f"Nao foi possivel ajustar ownership de {file_path}: {e}")

    def _finalize_output_files(self, *file_paths: Path):
        """Aplica ownership opcional aos artefatos gerados."""
        for file_path in file_paths:
            if file_path:
                self._apply_file_ownership(file_path)

    def _finalize_moved_input(self, file_path: Path):
        """Aplica ownership opcional ao arquivo movido para lido/."""
        self._apply_file_ownership(file_path)

    def create_month_folder(self, base_dir: Path, month_year: str) -> Path:
        """Cria pasta para o mes-ano se nao existir."""
        month_folder = base_dir / month_year
        month_folder.mkdir(exist_ok=True)
        return month_folder

    def _postprocess_transactions(self, transactions, account_name: str):
        """Wrapper de compatibilidade para a regra movida ao postprocessor."""
        return self.postprocessor.process(transactions, account_name)

    def _convert_with_processor_key(self, file_path: Path, key: str, validate: bool = True) -> bool:
        processor = self.registry.get(key)
        return self.pipeline.convert(file_path, processor, validate=validate)

    def convert_file(self, ofx_file: Path) -> bool:
        """Converte um arquivo OFX/QFX para CSV ezBookkeeping."""
        return self._convert_with_processor_key(ofx_file, 'ofx')

    def convert_mercadopago_file(self, csv_file: Path) -> bool:
        """Converte um arquivo CSV do Mercado Pago para CSV ezBookkeeping."""
        return self._convert_with_processor_key(csv_file, 'mercadopago')

    def convert_rico_file(self, csv_file: Path) -> bool:
        """Converte um arquivo CSV da Rico para CSV ezBookkeeping."""
        return self._convert_with_processor_key(csv_file, 'rico', validate=False)

    def convert_xp_cc_file(self, csv_file: Path) -> bool:
        """Converte um arquivo CSV de fatura XP CC para CSV ezBookkeeping."""
        return self._convert_with_processor_key(csv_file, 'xp_cc')

    def convert_xp_conta_file(self, csv_file: Path) -> bool:
        """Converte um arquivo CSV de extrato da conta digital XP para CSV ezBookkeeping."""
        return self._convert_with_processor_key(csv_file, 'xp_conta')

    def convert_rico_investimento_file(self, xlsx_file: Path) -> bool:
        """Converte um arquivo XLSX de investimentos da Rico/XP para CSV ezBookkeeping."""
        return self._convert_with_processor_key(xlsx_file, 'rico_investimento', validate=False)

    def convert_bb_file(self, csv_file: Path) -> bool:
        """Converte um arquivo CSV do Banco do Brasil para CSV ezBookkeeping."""
        return self._convert_with_processor_key(csv_file, 'bb')

    def scan_and_convert(self):
        """Escaneia pasta entrada e converte arquivos reconhecidos."""
        for file_path in self.entrada_dir.iterdir():
            if file_path.is_dir():
                continue

            processor = self.registry.find(file_path)
            if processor:
                self.pipeline.convert(file_path, processor, validate=False)
            else:
                logger.debug(f"Arquivo ignorado, formato não reconhecido: {file_path.name}")

    def watch(self):
        """Loop principal de monitoramento."""
        watch_interval = int(os.environ.get('WATCH_INTERVAL', 5))

        logger.info(f"Iniciando monitoramento v3.0 (intervalo: {watch_interval}s)")
        logger.info("Novo: Arquivos organizados automaticamente por mes-ano")
        logger.info("Suporte a CSV do Mercado Pago com deteccao de transferencias Pix")

        while True:
            try:
                self.scan_and_convert()
                time.sleep(watch_interval)
            except KeyboardInterrupt:
                logger.info("Monitoramento interrompido")
                break
            except Exception as e:
                logger.error(f"Erro no monitoramento: {e}")
                time.sleep(watch_interval)


if __name__ == '__main__':
    converter = OFXConverter()
    converter.watch()
