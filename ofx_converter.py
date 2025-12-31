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
    MercadoPagoParser,
    EZBookkeepingCSVWriter,
    RicoParser,
    RicoInvestimentoParser,
    XPCCParser,
    AccountMatcher
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
        
        # Parser Rico CSV
        self.rico_parser = RicoParser(self.categorizer)
        
        # Parser Rico Investimento XLSX
        self.rico_investimento_parser = RicoInvestimentoParser(self.categorizer)
        
        # Parser XP CC CSV
        self.xp_cc_parser = XPCCParser(
            self.text_normalizer,
            self.categorizer,
            self.date_extractor
        )
        
        # Account Matcher (identifica conta pelo nome do arquivo)
        contas_file = Path('/app/contas.yaml')
        self.account_matcher = AccountMatcher(
            config_file=str(contas_file) if contas_file.exists() else None
        )
        
        logger.info("OFX Converter v5.0 iniciado")
        logger.info(f"Monitorando pasta: {self.entrada_dir}")
        logger.info(f"Arquivos lidos organizados por mes em: {self.lido_dir}")
        logger.info(f"Arquivos convertidos organizados por mes em: {self.convertido_dir}")
        logger.info("Formatos suportados: OFX/QFX, Mercado Pago CSV, Rico CSV/XLSX, XP CC CSV")
        logger.info("Categorizacao automatica alinhada com ezBookkeeping")
    
    def create_month_folder(self, base_dir: Path, month_year: str) -> Path:
        """Cria pasta para o mes-ano se nao existir"""
        month_folder = base_dir / month_year
        month_folder.mkdir(exist_ok=True)
        return month_folder
    
    def convert_file(self, ofx_file: Path) -> bool:
        """
        Converte um arquivo OFX para CSV ezBookkeeping + QIF
        
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
            
            # Nomes dos arquivos de saída
            base_filename = ofx_file.stem
            csv_filename = f'{base_filename}.csv'
            qif_filename = f'{base_filename}.qif'
            
            csv_path = convertido_month_folder / csv_filename
            qif_path = convertido_month_folder / qif_filename
            
            # Converter - tentar com biblioteca ofxparse primeiro
            logger.info(f"Convertendo OFX: {ofx_file.name} -> {month_year}/{csv_filename} + {qif_filename}")
            
            transactions = self.ofx_parser.parse_with_ofxparse(ofx_file)
            
            # Se falhar, usar regex (fallback)
            if not transactions:
                logger.info("Método biblioteca falhou, tentando metodo regex...")
                transactions = self.ofx_parser.parse_with_regex(content)
            
            if transactions:
                # Identificar conta pelo nome do arquivo
                account_name = self.account_matcher.match_account(ofx_file.name) or ''
                
                # ====== ESCREVER CSV ======
                csv_writer = EZBookkeepingCSVWriter()
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

                
                csv_writer.close()
                logger.info(f"CSV ezBookkeeping salvo em: {csv_path}")
                
                # ====== ESCREVER QIF ======
                qif_writer = QIFWriter()
                qif_writer.create_qif_file(qif_path)
                
                for txn in transactions:
                    qif_writer.write_transaction(
                        txn['date'],
                        txn['amount'],
                        txn['description'],
                        txn['qif_category']
                    )
                
                qif_writer.close()
                logger.info(f"QIF salvo em: {qif_path}")
                
                # Mover arquivo para lido
                lido_path = lido_month_folder / ofx_file.name
                shutil.move(str(ofx_file), str(lido_path))
                
                logger.info(f"Conversao bem-sucedida: {ofx_file.name}")
                logger.info(f"Arquivo original movido para: {lido_path}")
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
        Converte um arquivo CSV do Mercado Pago para CSV ezBookkeeping + QIF
        
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
            
            # Usar nome original do CSV (sem extensão)
            base_filename = csv_file.stem
            csv_output_filename = f'{base_filename}.csv'
            qif_output_filename = f'{base_filename}.qif'
            
            csv_path = convertido_month_folder / csv_output_filename
            qif_path = convertido_month_folder / qif_output_filename
            
            # Identificar conta pelo nome do arquivo
            account_name = self.account_matcher.match_account(csv_file.name) or ''
            
            # ====== ESCREVER CSV ======
            csv_writer = EZBookkeepingCSVWriter()
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
            
            csv_writer.close()
            logger.info(f"CSV ezBookkeeping salvo em: {csv_path}")
            
            # ====== ESCREVER QIF ======
            qif_writer = QIFWriter()
            qif_writer.create_qif_file(qif_path)
            
            for txn in transactions:
                qif_writer.write_transaction(
                    txn['date'],
                    txn['amount'],
                    txn['description'],
                    txn['qif_category']  # Usa categoria QIF (com [] para transferências)
                )
            
            qif_writer.close()
            logger.info(f"QIF salvo em: {qif_path}")
            
            # Mover arquivo para lido
            lido_path = lido_month_folder / csv_file.name
            shutil.move(str(csv_file), str(lido_path))
            
            logger.info(f"Conversao bem-sucedida: {csv_file.name}")
            logger.info(f"Arquivo original movido para: {lido_path}")
            logger.info(f"Organizados na pasta: {month_year}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao converter CSV {csv_file.name}: {e}")
            return False
    
    def convert_rico_file(self, csv_file: Path) -> bool:
        """
        Converte um arquivo CSV da Rico para CSV ezBookkeeping + QIF
        
        Args:
            csv_file: Path do arquivo CSV
            
        Returns:
            True se conversao bem-sucedida
        """
        try:
            # Parsear CSV
            logger.info(f"Convertendo CSV Rico: {csv_file.name}")
            transactions = self.rico_parser.parse(str(csv_file))
            
            if not transactions:
                logger.error(f"Falha ao parsear CSV Rico: {csv_file.name}")
                return False
            
            # Extrair mes-ano das transacoes
            month_year = self.date_extractor.extract_month_year_from_transactions(
                [txn['date'] for txn in transactions]
            )
            
            # Criar pastas para o mes-ano
            lido_month_folder = self.create_month_folder(self.lido_dir, month_year)
            convertido_month_folder = self.create_month_folder(self.convertido_dir, month_year)
            
            # Usar nome original do CSV (sem extensão)
            base_filename = csv_file.stem
            csv_output_filename = f'{base_filename}.csv'
            qif_output_filename = f'{base_filename}.qif'
            
            csv_path = convertido_month_folder / csv_output_filename
            qif_path = convertido_month_folder / qif_output_filename
            
            # Identificar conta pelo nome do arquivo
            account_name = self.account_matcher.match_account(csv_file.name) or ''
            
            # ====== ESCREVER CSV ======
            csv_writer = EZBookkeepingCSVWriter()
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
            
            csv_writer.close()
            logger.info(f"CSV ezBookkeeping salvo em: {csv_path}")
            
            # ====== ESCREVER QIF ======
            qif_writer = QIFWriter()
            qif_writer.create_qif_file(qif_path)
            
            for txn in transactions:
                qif_writer.write_transaction(
                    txn['date'],
                    txn['amount'],
                    txn['description'],
                    txn['qif_category']
                )
            
            qif_writer.close()
            logger.info(f"QIF salvo em: {qif_path}")
            
            # Mover arquivo para lido
            lido_path = lido_month_folder / csv_file.name
            shutil.move(str(csv_file), str(lido_path))
            
            logger.info(f"Conversao bem-sucedida: {csv_file.name}")
            logger.info(f"Arquivo original movido para: {lido_path}")
            logger.info(f"Organizados na pasta: {month_year}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao converter CSV Rico {csv_file.name}: {e}")
            return False
    
    def convert_xp_cc_file(self, csv_file: Path) -> bool:
        """
        Converte um arquivo CSV de fatura XP CC para CSV ezBookkeeping + QIF
        
        Args:
            csv_file: Path do arquivo CSV
            
        Returns:
            True se conversao bem-sucedida
        """
        try:
            # Verificar se é CSV do XP CC
            if not XPCCParser.is_xp_cc_csv(csv_file):
                logger.warning(f"Arquivo CSV não é do XP CC: {csv_file.name}")
                return False
            
            # Parsear CSV
            logger.info(f"Convertendo CSV XP CC: {csv_file.name}")
            transactions = self.xp_cc_parser.parse_csv(csv_file)
            
            if not transactions:
                logger.error(f"Falha ao parsear CSV XP CC: {csv_file.name}")
                return False
            
            # Extrair mes-ano das transacoes
            month_year = self.date_extractor.extract_month_year_from_transactions(
                [txn['date'] for txn in transactions]
            )
            
            # Criar pastas para o mes-ano
            lido_month_folder = self.create_month_folder(self.lido_dir, month_year)
            convertido_month_folder = self.create_month_folder(self.convertido_dir, month_year)
            
            # Usar nome original do CSV (sem extensão)
            base_filename = csv_file.stem
            csv_output_filename = f'{base_filename}.csv'
            qif_output_filename = f'{base_filename}.qif'
            
            csv_path = convertido_month_folder / csv_output_filename
            qif_path = convertido_month_folder / qif_output_filename
            
            # Identificar conta pelo nome do arquivo
            account_name = self.account_matcher.match_account(csv_file.name) or ''
            
            # ====== ESCREVER CSV ======
            csv_writer = EZBookkeepingCSVWriter()
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
            
            csv_writer.close()
            logger.info(f"CSV ezBookkeeping salvo em: {csv_path}")
            
            # ====== ESCREVER QIF ======
            qif_writer = QIFWriter()
            qif_writer.create_qif_file(qif_path)
            
            for txn in transactions:
                qif_writer.write_transaction(
                    txn['date'],
                    txn['amount'],
                    txn['description'],
                    txn['qif_category']
                )
            
            qif_writer.close()
            logger.info(f"QIF salvo em: {qif_path}")
            
            # Mover arquivo para lido
            lido_path = lido_month_folder / csv_file.name
            shutil.move(str(csv_file), str(lido_path))
            
            logger.info(f"Conversao bem-sucedida: {csv_file.name}")
            logger.info(f"Arquivo original movido para: {lido_path}")
            logger.info(f"Organizados na pasta: {month_year}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao converter CSV XP CC {csv_file.name}: {e}")
            return False
    
    def convert_rico_investimento_file(self, xlsx_file: Path) -> bool:
        """
        Converte um arquivo XLSX de investimentos da Rico para CSV ezBookkeeping + QIF
        
        Args:
            xlsx_file: Path do arquivo XLSX
            
        Returns:
            True se conversao bem-sucedida
        """
        try:
            # Parsear XLSX
            logger.info(f"Convertendo XLSX Rico Investimento: {xlsx_file.name}")
            transactions = self.rico_investimento_parser.parse(str(xlsx_file))
            
            if not transactions:
                logger.error(f"Falha ao parsear XLSX Rico Investimento: {xlsx_file.name}")
                return False
            
            # Extrair mes-ano das transacoes
            month_year = self.date_extractor.extract_month_year_from_transactions(
                [txn['date'] for txn in transactions]
            )
            
            # Criar pastas para o mes-ano
            lido_month_folder = self.create_month_folder(self.lido_dir, month_year)
            convertido_month_folder = self.create_month_folder(self.convertido_dir, month_year)
            
            # Usar nome original do XLSX (sem extensão)
            base_filename = xlsx_file.stem
            csv_output_filename = f'{base_filename}.csv'
            qif_output_filename = f'{base_filename}.qif'
            
            csv_path = convertido_month_folder / csv_output_filename
            qif_path = convertido_month_folder / qif_output_filename
            
            # Identificar conta pelo nome do arquivo
            account_name = self.account_matcher.match_account(xlsx_file.name) or ''
            
            # ====== ESCREVER CSV ======
            csv_writer = EZBookkeepingCSVWriter()
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
            
            csv_writer.close()
            logger.info(f"CSV ezBookkeeping salvo em: {csv_path}")
            
            # ====== ESCREVER QIF ======
            qif_writer = QIFWriter()
            qif_writer.create_qif_file(qif_path)
            
            for txn in transactions:
                qif_writer.write_transaction(
                    txn['date'],
                    txn['amount'],
                    txn['description'],
                    txn['qif_category']
                )
            
            qif_writer.close()
            logger.info(f"QIF salvo em: {qif_path}")
            
            # Mover arquivo para lido
            lido_path = lido_month_folder / xlsx_file.name
            shutil.move(str(xlsx_file), str(lido_path))
            
            logger.info(f"Conversao bem-sucedida: {xlsx_file.name}")
            logger.info(f"Arquivo original movido para: {lido_path}")
            logger.info(f"Organizados na pasta: {month_year}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao converter XLSX Rico Investimento {xlsx_file.name}: {e}")
            return False

    def scan_and_convert(self):
        """Escaneia pasta entrada e converte arquivos OFX, CSV do Mercado Pago e Rico"""
        # Arquivos OFX
        ofx_files = [f for f in self.entrada_dir.iterdir() 
                     if f.is_file() and self.file_validator.is_valid_ofx_file(f)]
        
        # Arquivos XLSX de investimentos da Rico
        rico_xlsx_files = [f for f in self.entrada_dir.iterdir()
                           if f.is_file() and self.file_validator.is_valid_rico_investimento_xlsx(f)]
        
        # Arquivos CSV da Rico (tem "rico" no nome)
        rico_files = [f for f in self.entrada_dir.iterdir()
                      if f.is_file() and self.file_validator.is_valid_rico_csv(f)]
        
        # Arquivos CSV do XP CC (tem cabeçalho específico)
        xp_cc_files = [f for f in self.entrada_dir.iterdir()
                       if f.is_file() and self.file_validator.is_valid_xp_cc_csv(f)]
        
        # Arquivos CSV do Mercado Pago (CSV que NÃO é da Rico nem XP CC)
        csv_files = [f for f in self.entrada_dir.iterdir() 
                     if f.is_file() and self.file_validator.is_valid_mercadopago_csv(f)
                     and not self.file_validator.is_valid_rico_csv(f)
                     and not self.file_validator.is_valid_xp_cc_csv(f)]
        
        if ofx_files:
            logger.info(f"Encontrados {len(ofx_files)} arquivo(s) OFX para converter")
            for ofx_file in ofx_files:
                self.convert_file(ofx_file)
        
        if rico_xlsx_files:
            logger.info(f"Encontrados {len(rico_xlsx_files)} arquivo(s) XLSX Rico Investimento para converter")
            for rico_xlsx_file in rico_xlsx_files:
                self.convert_rico_investimento_file(rico_xlsx_file)
        
        if rico_files:
            logger.info(f"Encontrados {len(rico_files)} arquivo(s) CSV da Rico para converter")
            for rico_file in rico_files:
                self.convert_rico_file(rico_file)
        
        if xp_cc_files:
            logger.info(f"Encontrados {len(xp_cc_files)} arquivo(s) CSV do XP CC para converter")
            for xp_cc_file in xp_cc_files:
                self.convert_xp_cc_file(xp_cc_file)
        
        if csv_files:
            logger.info(f"Encontrados {len(csv_files)} arquivo(s) CSV do Mercado Pago para converter")
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
