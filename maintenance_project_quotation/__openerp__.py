# -*- coding: utf-8 -*-
##############################################################################
#
#    Elneo
#    Copyright (C) 2011-2015 Elneo (Technofluid SA) (<http://www.elneo.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': 'Maintenance Project Quotation',
    'version': '0.1',
    'category': 'Maintenance',
    'description': "Module to manage quotations based on maintenance projects",
    'author': 'Elneo',
    'website': 'http://www.elneo.com',
    'depends': ['maintenance_project', 'sale','base',],
    'data': ['maintenance_project_quotation.xml',
              'security/ir.model.access.csv','project_workflow.xml','installation_workflow.xml','user_quotation_request.xml'],
    'installable': True,
    'active': False,
    'application':False
}
