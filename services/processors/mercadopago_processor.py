#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Processor para CSV do Mercado Pago."""

from pathlib import Path

from services.mercadopago_parser import MercadoPagoParser


class MercadoPagoProcessor:
    key = 'mercadopago'
    name = 'CSV Mercado Pago'

    def __init__(self, mercadopago_parser):
        self.mercadopago_parser = mercadopago_parser

    def can_handle(self, file_path: Path) -> bool:
        return file_path.suffix.lower() == '.csv' and MercadoPagoParser.is_mercadopago_csv(file_path)

    def parse(self, file_path: Path):
        return self.mercadopago_parser.parse_csv(file_path)
