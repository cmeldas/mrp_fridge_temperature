from odoo.exceptions import AccessError
from odoo.modules.module import load_script
from odoo.tests import HttpCase, TransactionCase, new_test_user, tagged
from odoo.tools import file_path, mute_logger


@tagged('post_install', '-at_install')
class TestMrpFridgeTemperature(TransactionCase):
    """Lednice a záznamy teplot: překročení limitu a přístupová práva (ir.access v Odoo 20)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.mrp_user = new_test_user(cls.env, login='fridge_mrp_user', groups='mrp.group_mrp_user')
        cls.plain_user = new_test_user(cls.env, login='fridge_plain_user', groups='base.group_user')
        cls.fridge = cls.env['mrp.fridge'].create({'name': 'Lednice sýrárna'})

    def test_above_threshold(self):
        Temperature = self.env['mrp.fridge.temperature']
        cold = Temperature.create({'fridge_id': self.fridge.id, 'temperature': 4.5})
        warm = Temperature.create({'fridge_id': self.fridge.id, 'temperature': 9.0})
        self.assertTrue(cold.datetime)
        self.assertEqual(cold.threshold, 8.0)
        self.assertFalse(cold.is_above_threshold)
        self.assertTrue(warm.is_above_threshold)

        self.fridge.temperature_threshold = 10.0
        self.assertFalse(warm.is_above_threshold)
        self.assertEqual(self.fridge.temperature_ids, warm | cold)

    def test_access_mrp_user(self):
        fridge = self.env['mrp.fridge'].with_user(self.mrp_user).create({'name': 'Vitrína'})
        record = self.env['mrp.fridge.temperature'].with_user(self.mrp_user).create({
            'fridge_id': fridge.id,
            'temperature': 6.0,
        })
        record.temperature = 7.0
        self.assertEqual(record.read(['temperature'])[0]['temperature'], 7.0)
        record.unlink()
        fridge.unlink()

    def test_access_denied_without_mrp_group(self):
        with self.assertRaises(AccessError):
            self.env['mrp.fridge.temperature'].with_user(self.plain_user).search([])
        with self.assertRaises(AccessError):
            self.env['mrp.fridge'].with_user(self.plain_user).create({'name': 'Cizí'})


@tagged('post_install', '-at_install')
class TestMrpFridgeTemperatureJsonRpc(HttpCase):
    """Stejná volání jako blueprint Home Assistantu (odoo_fridge_yaml): /jsonrpc login + execute_kw create."""

    def test_home_assistant_blueprint_calls(self):
        if self.env['ir.module.module']._get('rpc').state != 'installed':
            self.skipTest("modul rpc (/jsonrpc) není nainstalovaný")
        user = new_test_user(self.env, login='ha_fridge_logger', groups='mrp.group_mrp_user')
        fridge = self.env['mrp.fridge'].create({'name': 'Lednice obchůdek'})
        db_name = self.env.cr.dbname

        with mute_logger('odoo.addons.rpc.controllers.jsonrpc'):
            uid = self.make_jsonrpc_request('/jsonrpc', {
                'service': 'common',
                'method': 'login',
                'args': [db_name, 'ha_fridge_logger', 'ha_fridge_logger'],
            })
            self.assertEqual(uid, user.id)
            record_id = self.make_jsonrpc_request('/jsonrpc', {
                'service': 'object',
                'method': 'execute_kw',
                'args': [
                    db_name, uid, 'ha_fridge_logger',
                    'mrp.fridge.temperature', 'create',
                    [{'fridge_id': fridge.id, 'temperature': 9.25}],
                ],
            })

        record = self.env['mrp.fridge.temperature'].browse(record_id)
        self.assertEqual(record.fridge_id, fridge)
        self.assertEqual(record.temperature, 9.25)
        self.assertTrue(record.is_above_threshold)
        self.assertEqual(record.create_uid, user)

    def test_home_assistant_api_key_scope(self):
        """Blueprint se na produkci přihlašuje API klíčem. Odoo 20 bere jen klíče se scope 'rpc';
        globální klíč z 19 (scope NULL) se už nepřihlásí, pre-migrate modulu ho převede na 'rpc'."""
        if self.env['ir.module.module']._get('rpc').state != 'installed':
            self.skipTest("modul rpc (/jsonrpc) není nainstalovaný")
        user = new_test_user(self.env, login='ha_fridge_apikey', groups='mrp.group_mrp_user')
        key = self.env['res.users.apikeys'].with_user(user).sudo()._generate('rpc', 'Homeassistant', None)
        db_name = self.env.cr.dbname

        def login():
            with mute_logger('odoo.addons.rpc.controllers.jsonrpc', 'odoo.addons.base.models.res_users'):
                return self.make_jsonrpc_request('/jsonrpc', {
                    'service': 'common',
                    'method': 'login',
                    'args': [db_name, 'ha_fridge_apikey', key],
                })

        self.assertEqual(login(), user.id)
        self.env.cr.execute("UPDATE res_users_apikeys SET scope = NULL WHERE user_id = %s", [user.id])
        self.assertFalse(login())

        # migrace modulu 19 -> 20 převede klíč s prázdným scope na 'rpc' a HA se zase přihlásí
        migration = load_script(
            file_path('mrp_fridge_temperature/migrations/20.0.1.0.0/pre-migrate.py'),
            'odoo.upgrade.mrp_fridge_temperature.test_pre_migrate',
        )
        with mute_logger('odoo.upgrade.mrp_fridge_temperature.test_pre_migrate'):
            migration.migrate(self.env.cr, '19.0.1.0.0')
        self.env.cr.execute("SELECT scope FROM res_users_apikeys WHERE user_id = %s", [user.id])
        self.assertEqual(self.env.cr.fetchall(), [('rpc',)])
        self.assertEqual(login(), user.id)
