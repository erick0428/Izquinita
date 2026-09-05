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
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
    ],

    'data': [
        'security/ir.model.access.csv',

        'views/variant.xml',
        'views/product.xml',
        'views/pos.xml',
        
        'views/views.xml',
        'views/templates.xml',
        'views/menu.xml',
    ],
    "assets": {
        "web.assets_backend": [
            "tindahan_pos/static/src/js/pos.js",
            "tindahan_pos/static/src/xml/pos.xml",
            "tindahan_pos/static/src/css/pos.css",
           
        ],
    },
    'demo': [
        'demo/demo.xml',
    ],

    'installable': True,
    'application': True,
}
