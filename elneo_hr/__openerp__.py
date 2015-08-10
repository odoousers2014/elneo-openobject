# -*- coding: utf-8 -*-

{
    'name': 'Elneo HR',
    'version': '0.1',
    'category': 'HR',
    'description': "Adapt hr to elneo specifics",
    'author': 'Elneo',
    'website': 'http://www.elneo.com',
    'depends': ['base','hr_equipment'],
    "data" : ['views/elneo_hr_view.xml', ],
    'installable': True,
    'auto_install': False,
    'application': True,
}