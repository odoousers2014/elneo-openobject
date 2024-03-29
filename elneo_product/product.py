from openerp import models, fields,api

class product_product(models.Model):
    _inherit = 'product.product'
    
    alias = fields.Char(string="Alias", size=255, translate=False)
    
    def _auto_init(self,cr,args):
        res = super(product_product, self)._auto_init(cr, args)
        cr.execute('SELECT indexname FROM pg_indexes WHERE indexname = \'product_product_alias_ext_name_index\'')
        if not cr.fetchone():
            cr.execute('CREATE INDEX product_product_alias_ext_name_index ON product_product (alias, default_code)')
            
        return res

class product_template(models.Model):
    _inherit = 'product.template'
    
    def _auto_init(self,cr,args):
        res = super(product_template, self)._auto_init(cr, args)
        cr.execute('SELECT indexname FROM pg_indexes WHERE indexname = \'product_template_ext_name_index\'')
        if not cr.fetchone():
            cr.execute('CREATE INDEX product_template_ext_name_index ON product_template (name)')
            
        '''
        cr.execute('SELECT indexname FROM pg_indexes WHERE indexname = \'product_supplierinfo_name_code_ext_name_index\'')
        if not cr.fetchone():
            cr.execute('CREATE INDEX product_supplierinfo_name_code_ext_name_index ON product_supplierinfo (product_name,product_code)')
            
        cr.execute('SELECT indexname FROM pg_indexes WHERE indexname = \'ir_translation_value_ext_name_index\'')
        if not cr.fetchone():
            cr.execute('CREATE INDEX ir_translation_value_ext_name_index ON ir_translation (value) WHERE name = \'product.template,name\'  ')
            
        '''
            
        return res
    
    def search_ext_name(self, name, args):
        text_to_search = None
        if args:
            text_to_search = args
       
                
        self.env.cr.execute("""
            select distinct product_product.id from product_product left join product_template on product_product.product_tmpl_id = product_template.id 
            left join product_supplierinfo on product_supplierinfo.product_tmpl_id = product_template.id 
            left join ir_translation on ir_translation.res_id = product_template.id and ir_translation.name = 'product.template,name' 
            where
            product_product.default_code ilike '%"""+text_to_search+"""%'
            or product_product.alias ilike '%"""+text_to_search+"""%' 
            or product_supplierinfo.product_name ilike '%"""+text_to_search+"""%' 
            or product_supplierinfo.product_code ilike '%"""+text_to_search+"""%'
            or ir_translation.value ilike '%"""+text_to_search+"""%' 
            or product_template.name ilike '%"""+text_to_search+"""%'
;""")
        
        res = self.env.cr.fetchall()
        return [('id', 'in', [x[0] for x in res])]
    
    @api.one
    def get_ext_name(self,field_name, arg):
        result = {}
        #products = self.browse(cr, uid, ids, context)
        #for product in products:        
        if self.alias:
            new_name = self.default_code+" "+self.alias
        else:
            new_name = result[self.id] = self.default_code
            
        for seller in self.seller_ids:
            if seller.product_code:
                new_name += " "+seller.product_code
        
        result[self.id] = new_name
                
        return result
    
    type = fields.Selection([('product', 'Stockable Product'),('consu', 'Consumable'),('service','Service')], 'Product Type', required=True,default='product', help="Consumable are product where you don't manage stock, a service is a non-material product provided by a company or an individual.")
    
    '''ext_name = fields.Text(compute=get_ext_name, method=True, string='Advanced search', search=search_ext_name)'''