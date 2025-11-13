{
    'name': 'MRP Fridge Temperature',
    'version': '18.0.1.0.0',
    'category': 'Manufacturing/Manufacturing',
    'summary': 'Track fridge temperatures in manufacturing',
    'description': """
        This module allows you to:
        * Manage fridges in manufacturing
        * Track fridge temperatures
        * View temperature history
    """,
    'author': 'Matouš Čmelík',
    'website': 'https://github.com/cmeldas',
    'maintainer': 'cmeldas@gmail.com',
    'depends': ['mrp'],
    'data': [
        'security/ir.model.access.csv',
        'views/mrp_fridge_views.xml',
        'views/mrp_fridge_temperature_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
