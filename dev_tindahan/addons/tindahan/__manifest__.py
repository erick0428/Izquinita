# -*- coding: utf-8 -*-
{
    'name': "tindahan",

    'summary': "Short (1 phrase/line) summary of the module's purpose",

    'description': """
Long description of module's purpose
    """,

    'author': "My Company",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        
        'data/sequence_data.xml',
        
        'views/employee.xml',
        'views/category.xml',
        'views/item_model.xml',
        'views/expenses.xml',
        'views/sales.xml',
        'views/attendance.xml',
        
        'wizards/business_performance_summary.xml',
        'wizards/wages_summary.xml',
        
        'views/menu.xml',
       
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}

