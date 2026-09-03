# -*- coding: utf-8 -*-
{
    'name': 'Tindahan POS',
    'summary': 'Point of Sale management',
    'description': '''
        Tindahan POS management module.
    ''',
    'author': 'My Company',
    'website': 'https://www.yourcompany.com',
    'category': 'Uncategorized',
    'version': '18.0.1.0.0',

    'depends': [
        'base',
        'mail',
    ],

    'data': [
        'security/ir.model.access.csv',

        'views/variant.xml',
        'views/product.xml',
        'views/views.xml',
        'views/templates.xml',
        'views/menu.xml',
    ],

    'demo': [
        'demo/demo.xml',
    ],

    'installable': True,
    'application': True,
}
