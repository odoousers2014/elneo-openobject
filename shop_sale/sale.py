from openerp import models, fields,api,_, workflow
from openerp.exceptions import Warning


class sale_order(models.Model):
    _inherit='sale.order'
    
    def _default_shop_sale(self):
        
        user = self.env['res.users'].search([('id','=',self.env.uid),('groups_id.name','=','Warehouse / Shop seller')])
        if user:
            return True
        else:
            return False
        
    @api.multi
    def print_invoice(self):
        '''
        This function prints the sales order invoice and mark it as sent, so that we can see more easily the next step of the workflow
        '''
        
        for invoice in self.invoice_ids:
            invoice.signal_workflow('invoice_open')
            
        assert len(self.invoice_ids) == 1, 'This option should only be used for a single id at a time.'
                
        return self.env['report'].get_action(self.invoice_ids, 'account.report_invoice')
    
    
    def shop_sale_ship(self):
        
        if self.shop_sale:
            for picking in self.picking_ids:
                for move in picking.move_lines:
                    #move.invoice_state='2binvoiced'
                    move.action_done()
                
            if not self.invoice_ids:
                picking.action_invoice_create(self.warehouse_id.shop_sale_journal_id.id, False)
            
            
            #for invoice in self.invoice_ids:
                #workflow.trg_validate(self.env.uid,'account.invoice', invoice.id, 'invoice_open',self.env.cr)
            
            return True
        return False
        
    def test_shop_sale(self):
        if self.shop_sale:
            for line in self.order_line:
                if line.route_id and line.route_id.name == 'Make To Order':
                    raise Warning(_('Error !'), _("You can't sell ordered products in a shop sale."))
            return True
        return False
    
    
    def action_invoice_create(self,grouped=False, states=None, date_inv = False,):
        res = super(sale_order, self).action_invoice_create(grouped, states, date_inv)
       
        if self.shop_sale and self.warehouse_id.shop_sale_journal_id:
            invoices = self.env['account.invoice'].browse(res)
            for invoice in invoices:
                invoice.shop_sale=True
                invoice.comment = self.note
                invoice.journal_id=self.warehouse_id.shop_sale_journal_id.id
          
    
    
    shop_sale=fields.Boolean("Shop Sale (Automatic Delivery)",default=_default_shop_sale)
    
    @api.onchange('shop_sale')
    def default_invoice_policy(self):
        if self.shop_sale:
            self.order_policy = 'manual'
            self.picking_policy = 'one'
    
sale_order()

class account_invoice(models.Model):
    _inherit = 'account.invoice'
    
    # Test function to get invoice open if it is a counter sale
    def shop_sale_invoice(self):
        return False
        for sale in self.env['sale.order'].search([('invoice_ids','in',self.id),('shop_sale','=',True)]):
            if self.state == 'draft':
                return True
        
        return False