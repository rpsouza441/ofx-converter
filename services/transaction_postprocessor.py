#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Transaction post-processing service.

Keeps account-specific adjustments outside the main converter flow.
"""

import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


class TransactionPostProcessor:
    """Aplica ajustes específicos após o parse bruto."""

    def process(self, transactions: List[Dict], account_name: str) -> List[Dict]:
        """
        Aplica regras de pós-processamento sem alterar contratos dos parsers.

        Hoje preserva a regra existente para faturas Nubank:
        "Pagamento recebido" no cartão vira transferência de pagamento de cartão.
        """
        if not account_name:
            return transactions

        normalized_account = account_name.strip().lower()

        for txn in transactions:
            description = (txn.get('description') or '').strip().lower()

            if normalized_account.startswith('cc nubank') and description == 'pagamento recebido':
                txn['type'] = 'transfer'
                txn['category'] = 'Transferência Geral'
                txn['subcategory'] = 'Pagamento de Cartão de Crédito'
                logger.info(
                    f"Post-processamento Nubank: '{txn.get('description')}' "
                    f"reclassificado como transferência para {account_name}"
                )

        return transactions
