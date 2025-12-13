#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OFX to QIF Converter v3.0
Conversor modular com services separados
"""

import os
import time
import shutil
import logging
from pathlib import Path

# Importar services
from services import (
    OFXFileReader,
    DateExtractor,
    TextNormalizer,
    TransactionCategorizer,
    QIFWriter,
    OFXParser,
    FileValidator,
    MercadoPagoParser
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
    """Conversor OFX para QIF usando arquitetura modular"""
    
    def __init__(self):
        self.entrada_dir = Path('/app/entrada')
        self.lido_dir = Path('/app/entrada/lido')
        self.convertido_dir = Path('/app/convertido')
        self.logs_dir = Path('/app/logs')
        
        # Criar diretorios
        for directory in [self.lido_dir, self.convertido_dir, self.logs_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Inicializar services
        self.file_reader = OFXFileReader()
        self.date_extractor = DateExtractor()
        self.text_normalizer = TextNormalizer()
        self.file_validator = FileValidator()
        
        # Tentar carregar categorias de arquivo YAML
        categorias_file = Path('/app/categorias.yaml')
        self.categorizer = TransactionCategorizer(
            rules_file=str(categorias_file) if categorias_file.exists() else None
        )
        
        # Parser OFX (precisa de text_normalizer, categorizer, date_extractor)
        self.ofx_parser = OFXParser(
            self.text_normalizer,
            self.categorizer,
            self.date_extractor
        )
        
        # Parser Mercado Pago CSV
        self.mercadopago_parser = MercadoPagoParser(
            self.text_normalizer,
            self.categorizer,
            self.date_extractor
        )
        
        logger.info("OFX Converter v3.0 iniciado")
        logger.info(f"Monitorando pasta: {self.entrada_dir}")
        logger.info(f"Arquivos lidos organizados por mes em: {self.lido_dir}")
        logger.info(f"Arquivos convertidos organizados por mes em: {self.convertido_dir}")
    
    def create_month_folder(self, base_dir: Path, month_year: str) -> Path:
        """Cria pasta para o mes-ano se nao existir"""
        month_folder = base_dir / month_year
        month_folder.mkdir(exist_ok=True)
        return month_folder
    
    def convert_file(self, ofx_file: Path) -> bool:
        """
        Converte um arquivo OFX para QIF
        
        Args:
            ofx_file: Path do arquivo OFX
            
        Returns:
            True se conversao bem-sucedida
        """
        try:
            # Ler arquivo OFX
            content = self.file_reader.read_with_encoding_detection(ofx_file)
            
            # Extrair mes-ano
            month_year = self.date_extractor.extract_month_year_from_ofx(content)
            
            # Criar pastas para o mes-ano
            lido_month_folder = self.create_month_folder(self.lido_dir, month_year)
            convertido_month_folder = self.create_month_folder(self.convertido_dir, month_year)
            
            # Caminho do QIF
            qif_filename = ofx_file.stem + '.qif'
            qif_path = convertido_month_folder / qif_filename
            
            # Converter - tentar com biblioteca ofxparse primeiro
            logger.info(f"Convertendo: {ofx_file.name} -> {month_year}/{qif_filename}")
            
            transactions = self.ofx_parser.parse_with_ofxparse(ofx_file)
            
            # Se falhar, usar regex (fallback)
            if not transactions:
                logger.info("Método biblioteca falhou, tentando metodo regex...")
                transactions = self.ofx_parser.parse_with_regex(content)
            
            if transactions:
                # Escrever QIF
                writer = QIFWriter()
                writer.create_qif_file(qif_path)
                
                for txn in transactions:
                    writer.write_transaction(
                        txn['date'],
                        txn['amount'],
                        txn['description'],
                        txn['category']
                    )
                
                writer.close()
                
                # Mover arquivo para lido
                lido_path = lido_month_folder / ofx_file.name
                shutil.move(str(ofx_file), str(lido_path))
                
                logger.info(f"Conversao bem-sucedida: {ofx_file.name}")
                logger.info(f"Arquivo movido para: {lido_path}")
                logger.info(f"QIF salvo em: {qif_path}")
                logger.info(f"Organizados na pasta: {month_year}")
                return True
            else:
                logger.error(f"Falha na conversao: {ofx_file.name}")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao converter {ofx_file.name}: {e}")
            return False
    
    def convert_mercadopago_file(self, csv_file: Path) -> bool:
        """
        Converte um arquivo CSV do Mercado Pago para QIF
        
        Args:
            csv_file: Path do arquivo CSV
            
        Returns:
            True se conversao bem-sucedida
        """
        try:
            # Verificar se é CSV do Mercado Pago
            if not MercadoPagoParser.is_mercadopago_csv(csv_file):
                logger.warning(f"Arquivo CSV não é do Mercado Pago: {csv_file.name}")
                return False
            
            # Parsear CSV
            logger.info(f"Convertendo CSV Mercado Pago: {csv_file.name}")
            transactions = self.mercadopago_parser.parse_csv(csv_file)
            
            if not transactions:
                logger.error(f"Falha ao parsear CSV: {csv_file.name}")
                return False
            
            # Extrair mes-ano das transacoes
            month_year = self.date_extractor.extract_month_year_from_transactions(
                [txn['date'] for txn in transactions]
            )
            
            # Criar pastas para o mes-ano
            lido_month_folder = self.create_month_folder(self.lido_dir, month_year)
            convertido_month_folder = self.create_month_folder(self.convertido_dir, month_year)
            
            # Nome do arquivo QIF: mercadopago_DD-MM-YYYY.qif
            first_date = self.mercadopago_parser.get_date_for_filename(csv_file)
            if first_date:
                qif_filename = f'mercadopago_{first_date}.qif'
            else:
                qif_filename = f'mercadopago_{csv_file.stem}.qif'
            
            qif_path = convertido_month_folder / qif_filename
            
            # Escrever QIF
            writer = QIFWriter()
            writer.create_qif_file(qif_path)
            
            for txn in transactions:
                writer.write_transaction(
                    txn['date'],
                    txn['amount'],
                    txn['description'],
                    txn['category']
                )
            
            writer.close()
            
            # Mover arquivo para lido
            lido_path = lido_month_folder / csv_file.name
            shutil.move(str(csv_file), str(lido_path))
            
            logger.info(f"Conversao bem-sucedida: {csv_file.name}")
            logger.info(f"Arquivo movido para: {lido_path}")
            logger.info(f"QIF salvo em: {qif_path}")
            logger.info(f"Organizados na pasta: {month_year}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao converter CSV {csv_file.name}: {e}")
            return False
    
    def scan_and_convert(self):
        """Escaneia pasta entrada e converte arquivos OFX e CSV do Mercado Pago"""
        # Arquivos OFX
        ofx_files = [f for f in self.entrada_dir.iterdir() 
                     if f.is_file() and self.file_validator.is_valid_ofx_file(f)]
        
        # Arquivos CSV do Mercado Pago
        csv_files = [f for f in self.entrada_dir.iterdir() 
                     if f.is_file() and self.file_validator.is_valid_mercadopago_csv(f)]
        
        if ofx_files:
            logger.info(f"Encontrados {len(ofx_files)} arquivo(s) OFX para converter")
            for ofx_file in ofx_files:
                self.convert_file(ofx_file)
        
        if csv_files:
            logger.info(f"Encontrados {len(csv_files)} arquivo(s) CSV para converter")
            for csv_file in csv_files:
                self.convert_mercadopago_file(csv_file)
    
    def watch(self):
        """Loop principal de monitoramento"""
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
