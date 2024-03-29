from openerp import models, fields, _, api
from openerp.exceptions import Warning
from openerp.tools.safe_eval import safe_eval
from datetime import datetime

class purchase_validation_wizard(models.TransientModel):
    _name = 'purchase.validation.wizard'
    #_description = 'Purchase validation wizard'
    
    purchase_validation_lines = fields.One2many('purchase.validation.line.wizard','purchase_validation_updater_id','Updated Lines')
    
    @api.model
    def default_get(self,fields):
        """
         To get default values for the object.
         @param fields: List of fields for which we want default values
         @return: A dictionary with default values for all field in ``fields``
        """
        
        
        purchase_validation_lines = []
        
            
        res = super(purchase_validation_wizard, self).default_get(fields)
        
        record_id = self.env.context and self.env.context.get('active_id', False) or False
        purchase = self.env['purchase.order'].browse(record_id)
       
        if purchase:
            for line in purchase.order_line:
                purchase_validation_lines.append({'purchase_line': line.id, 'name':line.name, 'new_price': line.price_unit, 'update_product':True, 'new_date_planned':line.date_planned})                
            if 'purchase_validation_lines' in fields:
                res.update({'purchase_validation_lines': purchase_validation_lines})
                
        return res
    
    def _get_sale_order_lines(self, purchase_validation_line):
        sale_lines = self.env['sale.order.line']
        for move in purchase_validation_line.purchase_line.move_ids:
            current_stock_move = move
            while current_stock_move:
                if current_stock_move.procurement_id.sale_line_id:
                    sale_lines = sale_lines | current_stock_move.procurement_id.sale_line_id
                    #sale_lines.append(current_stock_move.procurement_id.sale_line_id)
                current_stock_move = current_stock_move.move_dest_id
        return sale_lines
    
    @api.model
    def fields_view_get(self,view_id=None, view_type='form', toolbar=False, submenu=False):
        result = super(purchase_validation_wizard, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        if self.env.context and self.env.context.has_key('step') and self.env.context['step'] == 'warning':
            result['arch'] = '<form string="Warning">'
            result['arch'] += '<header><h3>Warning</h3></header>'
            
            for message in self.env.context.get('warning_message'):
                result['arch'] +='<p>'
                result['arch'] += '<label string="%s" colspan="4"/>'%(message.replace("\"", "&quot;"))
                result['arch'] += '<br />'
                result['arch'] +='</p>'
            
            result['arch'] += '<footer>'
            result['arch'] += '<button special="cancel" string="Ok" class="oe_highlight"/></footer></form>'
            
            
        if self.env.context and self.env.context.has_key('step') and self.env.context['step'] == 'warning_email':
            result['arch'] = '<form string="Warning">'
            result['arch'] += '<header><h3>Warning</h3></header>'
            for message in self.env.context.get('warning_message'):
                result['arch'] +='<p>'
                result['arch'] += '<label string="%s" colspan="4"/>'%(message.replace("\"", "&quot;"))
                result['arch'] += '<br />'
                result['arch'] +='</p>'
            result['arch'] += '<footer>'
            result['arch'] += '<button special="cancel" string="Close"/><button name="send_mail" type="object" string="Send email" class="oe_highlight"/></footer></form>'
            
        return result
    
    @api.multi
    def send_mail(self):
        
        if self.env.context.has_key("order_email"):
            
            email_template = self.browse(safe_eval(self.env['ir.config_parameter'].get_param('purchase_validation.email_template_id','False')))
            
            if not email_template:
                raise Warning(_("No Email Template is defined. Contact your Administrator"))
            
            
            if not self.env.user.partner_id.email:
                raise Warning(_("Please fill an email for user %s")%(self.env.user.name,))
        
            for order in self.env['sale.order'].browse(self.env.context.get('order_email')):
                order.confirmed_delivery_date = order.delivery_date
                values = self.env['email.template'].generate_email_batch(email_template.id, [order.id])
                values[order.id]['email_to']=order.partner_order_id.email
                values[order.id]['recipient_ids']=[(4, pid) for pid in values.get('partner_ids', list())]
                msg_id = self.env['mail.mail'].create(values[order.id])
        
                
        return True
    
    # Check if a price update is needed
    def _is_update_needed(self,line):
        
        #check if update is needed:
        need_update = True
        supplier_id = line.purchase_line.order_id.partner_id.id
        for supplierinfo in line.purchase_line.product_id.product_tmpl_id.seller_ids:
            if supplierinfo.name.id == supplier_id:
                for pricelist in supplierinfo.pricelist_ids: #depends technofluid_interne module, else use .pricelist_ids
                    if round(line.new_price,4) == round(line.purchase_line.price_unit,4) and\
                        line.price_quantity == pricelist.min_quantity and \
                        round(line.new_price,4) == round(pricelist.price,4) and \
                        (not line.new_discount or round(line.new_discount,4) == round(pricelist.discount,4)) and \
                        (not line.new_brut_price or round(line.new_brut_price,4) == round(pricelist.brut_price,4)):
                        need_update = False
                        break
            if not need_update:
                break
    
        return need_update
    
    def _update_delivery_date(self,line):
        #UPDATE DATE
        old_sale_order_delivery_date = {}
        stock_picking_to_update = set()
        sale_order_to_update=self.env['sale.order']
        if line.new_date_planned != line.purchase_line.date_planned:
            
            #compute difference between new date_planned and old date_planned
            difference = datetime.strptime(line.new_date_planned, '%Y-%m-%d') - datetime.strptime(line.purchase_line.date_planned, '%Y-%m-%d')
            
            #Update purchase_order_line
            line.purchase_line.write({'date_planned':line.new_date_planned})
            
            #Update reception
            stock_moves = self.env['stock.move'].search([('purchase_line_id', '=', line.purchase_line.id)])
            
            #stock_picking_to_update.update([stock_move.picking_id.id for stock_move in stock_moves])
            stock_moves.write({'date_expected':fields.Datetime.to_string(fields.Datetime.from_string(line.new_date_planned))})
            
            #update sale_order_line delay
            
            #for sale_line in  self._get_sale_order_lines(line):
            
                    
            for sale_line in  self._get_sale_order_lines(line):
                sale_line.write({'delay':sale_line.delay + difference.days})
                sale_order_to_update | sale_line.order_id
                #sale_order_to_update.add(sale_line.order_id)
                old_sale_order_delivery_date[sale_line.order_id.id] = sale_line.order_id.delivery_date
                
                
            #update delivery
            for move in stock_moves:
                current_stock_move = move
                while current_stock_move:
                    if current_stock_move.picking_id.picking_type_id.code == 'outgoing':
                        new_date = datetime.strptime(current_stock_move.date_expected, '%Y-%m-%d %H:%M:%S') + difference
                        current_stock_move.write({'date_expected':new_date.strftime('%Y-%m-%d %H:%M:%S'),'date':new_date.strftime('%Y-%m-%d %H:%M:%S')})
                        stock_picking_to_update.add(current_stock_move.picking_id)
                    current_stock_move = current_stock_move.move_dest_id
            
            for picking in stock_picking_to_update:
                picking.write({})
                
        return old_sale_order_delivery_date, sale_order_to_update
    
    def _get_date_message(self,old_dates={},warning_message=None,context=None):
        #check sale_order delivery date update :
        delivery_date_changes_email = []
        delivery_date_changes_noemail = []
        if warning_message is None :
            warning_message=[]
        
        if context is None:
            context={}
        
        for sale_order in self.env['sale.order'].browse(old_dates.keys()):
            if sale_order.delivery_date and datetime.strptime(sale_order.delivery_date, '%Y-%m-%d') > datetime.strptime(old_dates[sale_order.id], '%Y-%m-%d'):
                date_from_string = datetime.strptime(old_dates[sale_order.id], '%Y-%m-%d').strftime('%d/%m/%Y')
                date_to_string = datetime.strptime(sale_order.delivery_date, '%Y-%m-%d').strftime('%d/%m/%Y')
                warning_message.append(_("Delivery date of the sale order %s was postponed from %s to %s.")%(sale_order.name, date_from_string, date_to_string))
            if sale_order.confirmed_delivery_date and datetime.strptime(sale_order.confirmed_delivery_date, '%Y-%m-%d') < datetime.strptime(sale_order.delivery_date, '%Y-%m-%d'):
                confirmed_delivery_date = datetime.strptime(sale_order.confirmed_delivery_date, '%Y-%m-%d').strftime('%d/%m/%Y')
                warning_message.append(_("Delivery date confirmed to the customer (%s) for order %s is no longer correct.")%(confirmed_delivery_date, sale_order.name))
                if sale_order.partner_order_id and sale_order.partner_order_id.email: 
                    delivery_date_changes_email.append(sale_order)
                else:
                    delivery_date_changes_noemail.append(sale_order)
            
            if delivery_date_changes_noemail:
                warning_message.append(_('Some of customer have a delivery date that has changed, but order address has no email :\r\n'))
                for sale_order in delivery_date_changes_email:
                    warning_message.append('  - '+sale_order.partner_id.name+' - '+sale_order.name+' - '+datetime.strptime(sale_order.delivery_date, '%Y-%m-%d').strftime('%d/%m/%Y')+'\r\n')
            
            if delivery_date_changes_email:
                context['order_email'] = []
                warning_message.append(_('Do you want send an email to following customers about theses modifications :')+'\r\n')
                for sale_order in delivery_date_changes_email:
                    warning_message.append('  - '+sale_order.partner_id.name+' - '+sale_order.name+' - '+datetime.strptime(sale_order.delivery_date, '%Y-%m-%d').strftime('%d/%m/%Y')+' - '+sale_order.partner_order_id.email+'\r\n')
                    context['order_email'].append(sale_order.id)     
        
        return warning_message, delivery_date_changes_email, context
                    
    @api.multi         
    def update_purchase(self):
        # INIT #
        purchase_orders_to_update = self.env['purchase.order']
        old_sale_order_delivery_date = {}
        sale_orders_to_update = self.env['sale.order']
        warning_message = []
        
        for purchase_validation in self:
            for purchase_validation_line in purchase_validation.purchase_validation_lines:
                purchase_orders_to_update = purchase_orders_to_update | purchase_validation_line.purchase_line.order_id
                
                sale_lines = None
                
                #UPDATE PRICE
                if self._is_update_needed(purchase_validation_line):
                    #Update price in purchase order line
                    line = self.env['purchase.order.line'].browse([purchase_validation_line.purchase_line.id])
                    line.write({'price_unit':purchase_validation_line.new_price})
                    
                    
                    #Update price in invoice lines
                    #account_invoice_line_pool.write(cr, uid, [invoice_line.id for invoice_line in purchase_validation_line.purchase_line.invoice_lines if invoice_line.invoice_id.state == 'draft'], {'price_unit':purchase_validation_line.new_price}, context)
                    
                    #Update price in product
                    products = self.env['product.product'].browse([purchase_validation_line.purchase_line.product_id.id])
                    old_supplier_prices = products.update_price_for_supplier(purchase_validation_line.purchase_line.order_id.partner_id.commercial_partner_id.id, purchase_validation_line.new_price, purchase_validation_line.update_product,purchase_validation_line.new_brut_price, purchase_validation_line.price_quantity)                    
            
                    #Update price on invoice line
                    for purchase_invoice in purchase_validation_line.purchase_line.order_id.invoice_ids:
                        if purchase_invoice.state == 'draft':
                            for purchase_invoice_line in purchase_invoice.invoice_line:
                                if purchase_invoice_line.product_id.id == purchase_validation_line.purchase_line.product_id.id and purchase_invoice_line.quantity == purchase_validation_line.purchase_line.product_qty:
                                    purchase_invoice_line.write({'price_unit':purchase_validation_line.new_price})
                                    purchase_invoice.button_reset_taxes()
                   
                                                    
                    #reset old product supplier price
                    if not purchase_validation_line.update_product and old_supplier_prices:
                        products.update_price_for_supplier( purchase_validation_line.purchase_line.order_id.partner_id.id, old_supplier_prices[purchase_validation_line.purchase_line.product_id.id][0], purchase_validation_line.update_product, old_supplier_prices[purchase_validation_line.purchase_line.product_id.id][1],old_supplier_prices[purchase_validation_line.purchase_line.product_id.id][2], old_supplier_prices[purchase_validation_line.purchase_line.product_id.id][3], ignore_history=True)
                    else:
                        warning_message.append(_("Product '%s' price has been updated from %s to %s.")%(purchase_validation_line.purchase_line.product_id.name, old_supplier_prices[purchase_validation_line.purchase_line.product_id.id] and old_supplier_prices[purchase_validation_line.purchase_line.product_id.id][0] or '0', purchase_validation_line.new_price))
                        
                    sale_lines = self._get_sale_order_lines(purchase_validation_line)
                    sale_orders_to_update = sale_orders_to_update |  sale_lines.mapped('order_id')
                        
                old_dates, order_to_update = self._update_delivery_date(purchase_validation_line)
                
                
                sale_orders_to_update = sale_orders_to_update | order_to_update
                old_sale_order_delivery_date.update(old_dates)
        
        
        for sale_order_to_update in sale_orders_to_update:
            sale_order_to_update.write({})       
        
        purchase_orders_to_update.validated=True
        
        
        context = self._context.copy()
        
        warning_message, delivery_date_changes_email, ctx = self._get_date_message(old_sale_order_delivery_date,warning_message, context)
        
        context.update(ctx)
        
        if warning_message and warning_message != '':
            if delivery_date_changes_email:
                context['step'] = 'warning_email'
            else:
                context['step'] = 'warning'
            context['warning_message'] = warning_message
            return { 
                'view_type' : 'form', 
                'view_mode' : 'form', 
                'res_model' : 'purchase.validation.wizard', 
                'type' : 'ir.actions.act_window', 
                'target' : 'new', 
                'context' : context, 
            } 
        else:
            return {'type': 'ir.actions.act_window_close'}    
            
        
purchase_validation_wizard()

class purchase_validation_line_wizard(models.TransientModel):
    
    _name = 'purchase.validation.line.wizard'
    _description = 'Purchase updater line wizard'
 
    purchase_validation_updater_id = fields.Many2one('purchase.validation.wizard','Purchase Validation Wizard')
    purchase_line = fields.Many2one('purchase.order.line','Purchase Order Line')
    name = fields.Char('Name',size=64,readonly=True)
    update_product=fields.Boolean("Update Product Price ?")
    new_price = fields.Float("New Price",digits=(20,6))
    new_date_planned=fields.Date("Scheduled Date",index=True)
    new_brut_price=fields.Float("New Brut Price",digits=(20,6))
    new_discount=fields.Float("New Discount")
    price_quantity=fields.Float("Quantity",default=1)
 
    
purchase_validation_line_wizard()