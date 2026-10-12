"""Odoo 19 -> 20: přístupová práva na ir.access a API klíč pro Home Assistant.

1. Přístupová práva. V Odoo 20 nahradil model ``ir.access`` dřívější ``ir.model.access``
   a ``ir.rule``. Modul má v ``security/ir.access.csv`` stejná XML ID jako dřív
   v ``ir.model.access.csv`` (``access_mrp_fridge_user``, ``access_mrp_fridge_temperature_user``).
   Pokud v databázi z 19 ještě ukazují na model ``ir.model.access``, načtení CSV skončí chybou
   „found record of different model“. Proto se taková XML ID před aktualizací modulu odstraní
   a CSV pak založí nové záznamy ``ir.access``. Když už XML ID odstranila obecná migrace jádra
   (OpenUpgrade ``base`` pre-migration), nic se nestane. Staré řádky tabulky ``ir_model_access``
   zůstávají, jak je zvykem v OpenUpgrade.

2. API klíče bez scope. Home Assistant (blueprint ``odoo_fridge_yaml``) se přihlašuje přes
   ``/jsonrpc`` API klíčem. V 19 platil klíč s prázdným scope (``NULL``) jako globální pro
   všechna RPC, Odoo 20 hledá jen ``scope = 'rpc'`` a klíč s ``NULL`` už nikdy nepřihlásí.
   Teploty by se pak přestaly zapisovat bez chyby v Odoo. Klíče s ``NULL`` se proto převedou
   na ``rpc``, což je v 20 jediný scope pro RPC a odpovídá tomu, co klíč uměl v 19.
   Opakované spuštění nic nezmění.
"""
import logging

_logger = logging.getLogger(__name__)


def _drop_legacy_access_xmlids(cr):
    cr.execute(
        """
        DELETE FROM ir_model_data
         WHERE module = 'mrp_fridge_temperature'
           AND model IN ('ir.model.access', 'ir.rule')
     RETURNING name, model, res_id
        """
    )
    for name, model, res_id in cr.fetchall():
        _logger.info(
            "mrp_fridge_temperature: odstraněno XML ID %s (%s, id %s), nahradí ho ir.access",
            name, model, res_id,
        )


def _scope_global_api_keys(cr):
    cr.execute(
        """
        UPDATE res_users_apikeys
           SET scope = 'rpc'
         WHERE scope IS NULL
     RETURNING id, name, user_id
        """
    )
    for key_id, name, user_id in cr.fetchall():
        _logger.info(
            "mrp_fridge_temperature: API klíč %s „%s“ uživatele %s převeden ze scope NULL na 'rpc'",
            key_id, name, user_id,
        )


def migrate(cr, version):
    if not version:
        return
    _drop_legacy_access_xmlids(cr)
    _scope_global_api_keys(cr)
