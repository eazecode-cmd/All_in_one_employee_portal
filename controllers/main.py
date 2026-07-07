from odoo import http, _, fields
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal
import base64
from datetime import datetime, timedelta


class EmployeePortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        employee = request.env.user.employee_id
        if employee and employee.grant_portal_access:
            stats = employee.get_portal_dashboard_stats() or {}
            
            # Count unread announcements
            announcements = request.env['portal.announcement'].sudo().get_active_announcements(employee.id)
            unread_count = len(announcements.filtered(lambda a: employee not in a.read_employee_ids))
            stats['unread_announcements_count'] = unread_count
            
            values.update({
                'employee': employee,
                'dashboard_stats': stats,
            })
        else:
            values.update({
                'employee': False,
                'dashboard_stats': {
                    'attendance_status': 'checked_out',
                    'leave_balance': 0,
                    'upcoming_tasks': 0,
                    'unread_announcements_count': 0,
                },
            })
        return values

    @http.route(['/my/profile', '/my/profile/edit'], type='http', auth="user", website=True)
    def portal_my_profile(self, **kw):
        employee = request.env.user.employee_id
        if not employee:
            return request.redirect('/my')
        
        if http.request.httprequest.method == 'POST':
            # Handle profile update
            values = {}
            if kw.get('name'):
                values['name'] = kw.get('name')
            if kw.get('work_phone') is not None:
                values['work_phone'] = kw.get('work_phone')
            if kw.get('work_email') is not None:
                values['work_email'] = kw.get('work_email')
            if kw.get('private_phone') is not None:
                values['private_phone'] = kw.get('private_phone')
            if kw.get('private_email') is not None:
                values['private_email'] = kw.get('private_email')
            if kw.get('birthday'):
                values['birthday'] = kw.get('birthday')
            if kw.get('private_street') is not None:
                values['private_street'] = kw.get('private_street')
            
            if 'image_1920' in request.httprequest.files:
                file = request.httprequest.files['image_1920']
                if file and file.filename:
                    values['image_1920'] = base64.b64encode(file.read())
            
            if values:
                employee.sudo().write(values)
            return request.redirect('/my/profile?success=1')

        values = {
            'employee': employee,
            'page_name': 'my_profile',
            'success': kw.get('success'),
        }
        return request.render("All_in_one_employee_portal.portal_my_profile", values)

    @http.route(['/my/attendance'], type='http', auth="user", website=True)
    def portal_my_attendance(self, **kw):
        employee = request.env.user.employee_id
        if not employee:
            return request.redirect('/my')
        
        attendances = request.env['hr.attendance'].sudo().search([
            ('employee_id', '=', employee.id)
        ], limit=10, order='check_in desc')
        
        values = {
            'employee': employee,
            'attendances': attendances,
            'page_name': 'attendance',
        }
        return request.render("All_in_one_employee_portal.portal_my_attendance", values)

    @http.route(['/my/attendance/toggle'], type='json', auth="user", methods=['POST'], website=True)
    def portal_attendance_toggle(self, latitude=None, longitude=None, **kw):
        employee = request.env.user.employee_id
        if not employee:
            return {'error': 'Employee not found'}
        
        attendance = employee.action_portal_attendance_toggle(latitude, longitude)
        return {
            'status': employee.attendance_state,
            'check_in': attendance.check_in,
            'check_out': attendance.check_out,
        }

    @http.route(['/my/leaves'], type='http', auth="user", website=True)
    def portal_my_leaves(self, **kw):
        employee = request.env.user.employee_id
        if not employee:
            return request.redirect('/my')
        
        # Get all active leave types
        leave_types = request.env['hr.leave.type'].sudo().search([
            ('active', '=', True)
        ])
        
        # Robustly fetch and clean allocation data for Odoo 18
        balances = []
        try:
            balances_data = leave_types.get_allocation_data(employee)
            raw_balances = balances_data.get(employee, [])
            
            # Ensure raw_balances is a list or tuple we can iterate
            if not isinstance(raw_balances, (list, tuple)):
                raw_balances = [raw_balances] if raw_balances else []
                
            for item in raw_balances:
                if isinstance(item, dict):
                    balances.append(item)
                elif isinstance(item, (list, tuple)) and len(item) > 0:
                    # If it's a nested structure, try to find the dict inside
                    for sub_item in item:
                        if isinstance(sub_item, dict):
                            balances.append(sub_item)
        except Exception as e:
            # Fallback to empty list if something goes wrong
            balances = []
            
        # Get leave history
        leaves = request.env['hr.leave'].sudo().search([
            ('employee_id', '=', employee.id)
        ], order='date_from desc')
        
        values = {
            'employee': employee,
            'balances': balances,
            'leaves': leaves,
            'leave_types': leave_types,
            'page_name': 'leaves',
            'success': kw.get('success'),
            'error': kw.get('error'),
        }
        return request.render("All_in_one_employee_portal.portal_my_leaves", values)

    @http.route(['/my/leaves/apply'], type='http', auth="user", methods=['POST'], website=True)
    def portal_my_leaves_apply(self, **kw):
        employee = request.env.user.employee_id
        if not employee:
            return request.redirect('/my')
        
        try:
            request.env['hr.leave'].sudo().create({
                'name': kw.get('name') or 'Leave Request',
                'holiday_status_id': int(kw.get('holiday_status_id')),
                'request_date_from': kw.get('date_from'),
                'request_date_to': kw.get('date_to'),
                'employee_id': employee.id,
                'request_unit_hours': False,
            })
            return request.redirect('/my/leaves?success=1')
        except Exception as e:
            return request.redirect('/my/leaves?error=%s' % str(e))

    @http.route(['/my/payroll'], type='http', auth="user", website=True)
    def portal_my_payroll(self, **kw):
        employee = request.env.user.employee_id
        if not employee:
            return request.redirect('/my')
        
        # Get payslips for the employee
        payslips = request.env['hr.payslip'].sudo().search([
            ('employee_id', '=', employee.id),
            ('state', 'in', ['done', 'paid'])
        ], order='date_from desc')
        
        values = {
            'employee': employee,
            'payslips': payslips,
            'page_name': 'payroll',
        }
        return request.render("All_in_one_employee_portal.portal_my_payroll", values)

    @http.route(['/my/payslip/download/<int:payslip_id>'], type='http', auth="user", website=True)
    def portal_payslip_download(self, payslip_id, **kw):
        employee = request.env.user.employee_id
        if not employee:
            return request.redirect('/my')
        
        # Search for the payslip belonging to this employee
        payslip = request.env['hr.payslip'].sudo().search([
            ('id', '=', payslip_id),
            ('employee_id', '=', employee.id)
        ], limit=1)
        
        if not payslip:
            return request.redirect('/my/payroll')

        # Generate the PDF report using sudo to bypass security restrictions
        pdf_content, content_type = request.env['ir.actions.report'].sudo()._render_qweb_pdf(
            'hr_payroll.action_report_payslip', [payslip.id]
        )
        
        pdfhttpheaders = [
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(pdf_content)),
            ('Content-Disposition', 'attachment; filename="%s.pdf"' % payslip.number)
        ]
        return request.make_response(pdf_content, headers=pdfhttpheaders)

    @http.route(['/my/tasks'], type='http', auth="user", website=True)
    def portal_my_tasks(self, **kw):
        employee = request.env.user.employee_id
        if not employee:
            return request.redirect('/my')
        
        tasks = request.env['project.task'].sudo().search([
            ('employee_id', '=', employee.id)
        ], order='create_date desc')
        
        values = {
            'employee': employee,
            'tasks': tasks,
            'page_name': 'tasks',
        }
        return request.render("All_in_one_employee_portal.portal_my_tasks", values)

    @http.route(['/my/task/<int:task_id>'], type='http', auth="user", website=True)
    def portal_my_task_detail(self, task_id, **kw):
        employee = request.env.user.employee_id
        if not employee:
            return request.redirect('/my')
        
        task = request.env['project.task'].sudo().search([
            ('id', '=', task_id),
            ('employee_id', '=', employee.id)
        ], limit=1)
        
        if not task:
            return request.redirect('/my/tasks')
        
        # Calculate elapsed time if started
        elapsed_time = ""
        if task.is_task_started and task.task_start_time:
            diff = fields.Datetime.now() - task.task_start_time
            hours, remainder = divmod(diff.total_seconds(), 3600)
            minutes, seconds = divmod(remainder, 60)
            elapsed_time = "%02d:%02d:%02d" % (hours, minutes, seconds)

        values = {
            'employee': employee,
            'task': task,
            'page_name': 'tasks',
            'elapsed_time': elapsed_time,
        }
        return request.render("All_in_one_employee_portal.portal_my_task_detail", values)

    @http.route(['/my/task/start/<int:task_id>'], type='http', auth="user", website=True)
    def portal_my_task_start(self, task_id, **kw):
        employee = request.env.user.employee_id
        task = request.env['project.task'].sudo().search([
            ('id', '=', task_id),
            ('employee_id', '=', employee.id)
        ], limit=1)
        if task and not task.is_task_started:
            task.sudo().write({
                'is_task_started': True,
                'task_start_time': fields.Datetime.now(),
                'state': '02_changes_requested' # Or any "In Progress" equivalent stage
            })
        return request.redirect('/my/task/%s' % task_id)

    @http.route(['/my/task/finish/<int:task_id>'], type='http', auth="user", website=True)
    def portal_my_task_finish(self, task_id, **kw):
        employee = request.env.user.employee_id
        task = request.env['project.task'].sudo().search([
            ('id', '=', task_id),
            ('employee_id', '=', employee.id)
        ], limit=1)
        if task and task.is_task_started:
            # Calculate duration in hours
            start_time = task.task_start_time
            end_time = fields.Datetime.now()
            duration_seconds = (end_time - start_time).total_seconds()
            duration_hours = max(0.01, duration_seconds / 3600.0) # Minimum 0.01 hour to avoid 0
            
            # Create Timesheet Entry Automatically
            request.env['account.analytic.line'].sudo().create({
                'name': 'Portal: Completed Task',
                'task_id': task.id,
                'project_id': task.project_id.id,
                'employee_id': employee.id,
                'unit_amount': duration_hours,
                'date': fields.Date.today(),
            })

            task.sudo().write({
                'is_task_started': False,
                'state': '1_done' # Moved to Done
            })
        return request.redirect('/my/task/%s' % task_id)

    @http.route(['/my/task/reopen/<int:task_id>'], type='http', auth="user", website=True)
    def portal_my_task_reopen(self, task_id, **kw):
        employee = request.env.user.employee_id
        task = request.env['project.task'].sudo().search([
            ('id', '=', task_id),
            ('employee_id', '=', employee.id)
        ], limit=1)
        if task:
            task.sudo().write({
                'state': '01_in_progress',
                'is_task_started': False
            })
        return request.redirect('/my/task/%s' % task_id)

    @http.route(['/my/timesheets'], type='http', auth="user", website=True)
    def portal_my_timesheets(self, **kw):
        employee = request.env.user.employee_id
        if not employee:
            return request.redirect('/my')
        
        timesheets = request.env['account.analytic.line'].sudo().search([
            ('employee_id', '=', employee.id),
            ('project_id', '!=', False)
        ], limit=20, order='date desc')
        
        tasks = request.env['project.task'].sudo().search([
            ('employee_id', '=', employee.id)
        ])
        
        values = {
            'employee': employee,
            'timesheets': timesheets,
            'tasks': tasks,
            'page_name': 'timesheets',
            'success': kw.get('success'),
            'error': kw.get('error'),
        }
        return request.render("All_in_one_employee_portal.portal_my_timesheets", values)

    @http.route(['/my/timesheets/log'], type='http', auth="user", methods=['POST'], website=True)
    def portal_timesheets_log(self, **kw):
        employee = request.env.user.employee_id
        if not employee:
            return request.redirect('/my')
        
        try:
            task = request.env['project.task'].sudo().browse(int(kw.get('task_id')))
            request.env['account.analytic.line'].sudo().create({
                'name': kw.get('name') or 'Work log',
                'project_id': task.project_id.id,
                'task_id': task.id,
                'employee_id': employee.id,
                'date': kw.get('date') or fields.Date.today(),
                'unit_amount': float(kw.get('unit_amount')),
            })
            return request.redirect('/my/timesheets?success=1')
        except Exception as e:
            return request.redirect('/my/timesheets?error=%s' % str(e))

    @http.route(['/my/expenses'], type='http', auth="user", website=True)
    def portal_my_expenses(self, **kw):
        employee = request.env.user.employee_id
        if not employee:
            return request.redirect('/my')
        
        expenses = request.env['hr.expense'].sudo().search([
            ('employee_id', '=', employee.id)
        ], order='date desc')
        
        # Get active products that can be expensed
        expense_categories = request.env['product.product'].sudo().search([
            ('can_be_expensed', '=', True)
        ])
        
        # Get active currencies
        currencies = request.env['res.currency'].sudo().search([
            ('active', '=', True)
        ])
        
        # Compute which expenses have attachments (attachment_number field not available via portal)
        expense_ids_with_attachment = set()
        if expenses:
            attachments = request.env['ir.attachment'].sudo().search([
                ('res_model', '=', 'hr.expense'),
                ('res_id', 'in', expenses.ids)
            ])
            expense_ids_with_attachment = set(attachments.mapped('res_id'))
        
        values = {
            'employee': employee,
            'expenses': expenses,
            'expense_categories': expense_categories,
            'currencies': currencies,
            'expense_ids_with_attachment': expense_ids_with_attachment,
            'page_name': 'expenses',
            'success': kw.get('success'),
            'error': kw.get('error'),
        }
        return request.render("All_in_one_employee_portal.portal_my_expenses", values)

    @http.route(['/my/expense/submit'], type='http', auth="user", methods=['POST'], website=True)
    def portal_expense_submit(self, **kw):
        employee = request.env.user.employee_id
        if not employee:
            return request.redirect('/my')
        
        try:
            # In Odoo 18, hr.expense was refactored:
            # - total_amount_currency is the PRIMARY writable amount field (what user enters)
            # - price_unit is COMPUTED from total_amount_currency / quantity
            # - Writing price_unit directly gets overridden by @api.depends compute
            submitted_amount = float(kw.get('unit_amount') or 0.0)
            
            # Create expense claim
            expense_vals = {
                'name': kw.get('name') or 'Expense Claim',
                'product_id': int(kw.get('product_id')),
                'total_amount_currency': submitted_amount,
                'quantity': 1.0,
                'date': kw.get('date') or fields.Date.today(),
                'employee_id': employee.id,
                'payment_mode': kw.get('payment_mode') or 'own_account',
                'currency_id': int(kw.get('currency_id') or employee.company_id.currency_id.id),
            }
            
            expense = request.env['hr.expense'].sudo().create(expense_vals)
            
            # Safety: ensure the amount was persisted correctly after ORM computes ran
            if submitted_amount and expense.total_amount_currency != submitted_amount:
                expense.sudo().write({'total_amount_currency': submitted_amount})

            
            if 'receipt_file' in request.httprequest.files:
                file = request.httprequest.files['receipt_file']
                if file and file.filename:
                    attachment_data = base64.b64encode(file.read())
                    request.env['ir.attachment'].sudo().create({
                        'name': file.filename,
                        'res_model': 'hr.expense',
                        'res_id': expense.id,
                        'datas': attachment_data,
                        'type': 'binary',
                    })
            
            return request.redirect('/my/expenses?success=1')
        except Exception as e:
            return request.redirect('/my/expenses?error=%s' % str(e))

    @http.route(['/my/expense/receipt/<int:expense_id>'], type='http', auth="user", website=True)
    def portal_expense_receipt(self, expense_id, **kw):
        employee = request.env.user.employee_id
        if not employee:
            return request.redirect('/my')
        
        # Ensure expense belongs to this employee
        expense = request.env['hr.expense'].sudo().search([
            ('id', '=', expense_id),
            ('employee_id', '=', employee.id)
        ], limit=1)
        if not expense:
            return request.redirect('/my/expenses')
        
        attachment = request.env['ir.attachment'].sudo().search([
            ('res_model', '=', 'hr.expense'),
            ('res_id', '=', expense.id)
        ], limit=1)
        if not attachment:
            return request.redirect('/my/expenses')
        
        filecontent = base64.b64decode(attachment.datas)
        headers = [
            ('Content-Type', attachment.mimetype),
            ('Content-Length', len(filecontent)),
            ('Content-Disposition', 'attachment; filename="%s"' % attachment.name)
        ]
        return request.make_response(filecontent, headers=headers)

    @http.route(['/my/schedule'], type='http', auth="user", website=True)
    def portal_my_schedule(self, week=None, **kw):
        employee = request.env.user.employee_id
        if not employee:
            return request.redirect('/my')
        
        today = fields.Date.today()
        # Find Monday of this week
        monday = today - timedelta(days=today.weekday())
        
        if week == 'next':
            monday = monday + timedelta(days=7)
            week_type = 'next'
        else:
            week_type = 'current'
            
        sunday = monday + timedelta(days=6)
        
        # Datetime boundaries (UTC)
        start_dt = datetime.combine(monday, datetime.min.time())
        end_dt = datetime.combine(sunday, datetime.max.time())
        
        # Search slots for this employee in the week
        slots = request.env['planning.slot'].sudo().search([
            ('employee_id', '=', employee.id),
            ('start_datetime', '>=', start_dt),
            ('end_datetime', '<=', end_dt)
        ], order='start_datetime asc')
        
        # Structure the days of the week
        days_info = [
            {'name': 'Monday', 'date': monday, 'shifts': []},
            {'name': 'Tuesday', 'date': monday + timedelta(days=1), 'shifts': []},
            {'name': 'Wednesday', 'date': monday + timedelta(days=2), 'shifts': []},
            {'name': 'Thursday', 'date': monday + timedelta(days=3), 'shifts': []},
            {'name': 'Friday', 'date': monday + timedelta(days=4), 'shifts': []},
            {'name': 'Saturday', 'date': monday + timedelta(days=5), 'shifts': []},
            {'name': 'Sunday', 'date': monday + timedelta(days=6), 'shifts': []},
        ]
        
        total_hours = 0.0
        primary_role = 'Generalist'
        role_counts = {}
        
        for slot in slots:
            slot_date = fields.Date.to_date(slot.start_datetime)
            for day in days_info:
                if day['date'] == slot_date:
                    day['shifts'].append(slot)
                    hours = slot.allocated_hours or 0.0
                    if not hours and slot.start_datetime and slot.end_datetime:
                        hours = (slot.end_datetime - slot.start_datetime).total_seconds() / 3600.0
                    total_hours += hours
                    if slot.role_id:
                        role_counts[slot.role_id.name] = role_counts.get(slot.role_id.name, 0) + 1
        
        if role_counts:
            primary_role = max(role_counts, key=role_counts.get)
            
        values = {
            'employee': employee,
            'days_info': days_info,
            'week_type': week_type,
            'monday': monday,
            'sunday': sunday,
            'total_shifts': len(slots),
            'total_hours': total_hours,
            'primary_role': primary_role,
            'page_name': 'schedule',
        }
        return request.render("All_in_one_employee_portal.portal_my_schedule", values)

    @http.route(['/my/leads', '/my/leads/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_leads(self, page=1, search=None, filterby=None, **kw):
        employee = request.env.user.employee_id
        if not employee:
            return request.redirect('/my')
            
        CrmLead = request.env['crm.lead'].sudo()
        domain = [('user_id', '=', request.env.user.id)]
        
        # Handle search filters
        if search:
            domain += ['|', '|', ('name', 'ilike', search), ('partner_name', 'ilike', search), ('contact_name', 'ilike', search)]
            
        # Handle Pipeline vs Closed filters
        if filterby == 'closed':
            domain += [('active', '=', True), '|', ('stage_id.is_won', '=', True), ('stage_id.fold', '=', True)]
        else:
            domain += [('active', '=', True), ('stage_id.is_won', '=', False), ('stage_id.fold', '=', False)]
            
        # Create Lead request (POST)
        if http.request.httprequest.method == 'POST' and kw.get('action') == 'create_lead':
            CrmLead.create({
                'name': kw.get('name'),
                'partner_name': kw.get('partner_name'),
                'contact_name': kw.get('contact_name'),
                'email_from': kw.get('email'),
                'phone': kw.get('phone'),
                'expected_revenue': float(kw.get('expected_revenue') or 0.0),
                'description': kw.get('description'),
                'user_id': request.env.user.id,
                'type': 'opportunity',
            })
            return request.redirect('/my/leads?success=1')
            
        # Stats computation (Retrieve all assigned leads/opportunities)
        all_assigned = CrmLead.search([('user_id', '=', request.env.user.id)])
        total_opportunities = len(all_assigned.filtered(lambda l: not l.stage_id.is_won and not l.stage_id.fold))
        pipeline_value = sum(all_assigned.filtered(lambda l: not l.stage_id.is_won and not l.stage_id.fold).mapped('expected_revenue'))
        
        won_leads = all_assigned.filtered(lambda l: l.stage_id.is_won)
        win_rate = (len(won_leads) / len(all_assigned) * 100) if all_assigned else 0.0
        win_rate_str = '%.1f%%' % win_rate
        pipeline_value_str = '$ %.2f' % pipeline_value
        
        # Fetch filtered leads for view
        leads = CrmLead.search(domain, order='priority desc, create_date desc')
        
        # Pre-format each lead's expected_revenue as string to avoid QWeb format issues
        leads_data = []
        for lead in leads:
            leads_data.append({
                'lead': lead,
                'expected_revenue_str': '$ %.2f' % (lead.expected_revenue or 0.0),
                'probability_str': '%d%%' % (lead.probability or 0),
            })
        
        values = {
            'employee': employee,
            'leads': leads,
            'leads_data': leads_data,
            'search': search,
            'filterby': filterby or 'pipeline',
            'total_opportunities': total_opportunities,
            'pipeline_value_str': pipeline_value_str,
            'win_rate_str': win_rate_str,
            'success': kw.get('success'),
            'page_name': 'crm_leads',
        }
        return request.render("All_in_one_employee_portal.portal_my_leads", values)

    @http.route(['/my/lead/<int:lead_id>'], type='http', auth="user", website=True)
    def portal_my_lead_detail(self, lead_id, **kw):
        employee = request.env.user.employee_id
        if not employee:
            return request.redirect('/my')
            
        lead = request.env['crm.lead'].sudo().browse(lead_id)
        if not lead.exists() or lead.user_id.id != request.env.user.id:
            return request.redirect('/my/leads')
            
        # Handle log note submission (POST)
        if http.request.httprequest.method == 'POST' and kw.get('action') == 'log_note':
            new_note = kw.get('new_note')
            if new_note:
                lead.message_post(body=new_note, subtype_xmlid="mail.mt_note")
            return request.redirect(f'/my/lead/{lead_id}?success_note=1')
            
        # Fetch CRM Stages for pipeline visual
        stages = request.env['crm.stage'].sudo().search([], order='sequence asc')
        
        values = {
            'employee': employee,
            'lead': lead,
            'stages': stages,
            'success_note': kw.get('success_note'),
            'page_name': 'crm_leads',
        }
        return request.render("All_in_one_employee_portal.portal_lead_detail", values)

    @http.route(['/my/sales', '/my/sales/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_sales(self, page=1, search=None, filterby=None, **kw):
        employee = request.env.user.employee_id
        if not employee:
            return request.redirect('/my')
            
        SaleOrder = request.env['sale.order'].sudo()
        domain = [('user_id', '=', request.env.user.id)]
        
        # Handle search filters
        if search:
            domain += ['|', '|', ('name', 'ilike', search), ('partner_id.name', 'ilike', search), ('state', 'ilike', search)]
            
        # Handle Quotation vs Confirmed Sale Orders filters
        if filterby == 'orders':
            domain += [('state', 'in', ('sale', 'done'))]
        elif filterby == 'quotes':
            domain += [('state', 'in', ('draft', 'sent'))]
            
        # Retrieve all assigned orders for stats
        all_assigned = SaleOrder.search([('user_id', '=', request.env.user.id)])
        total_orders = len(all_assigned)
        sales_value = sum(all_assigned.filtered(lambda o: o.state in ('sale', 'done')).mapped('amount_total'))
        sales_value_str = '$ %.2f' % sales_value
        
        confirmed_orders = all_assigned.filtered(lambda o: o.state in ('sale', 'done'))
        conversion_rate = (len(confirmed_orders) / len(all_assigned) * 100) if all_assigned else 0.0
        conversion_rate_str = '%.1f%%' % conversion_rate
        
        # Fetch filtered orders for view
        orders = SaleOrder.search(domain, order='date_order desc, id desc')
        
        orders_data = []
        for order in orders:
            orders_data.append({
                'order': order,
                'amount_total_str': '$ %.2f' % (order.amount_total or 0.0),
                'date_order_str': order.date_order.strftime('%Y-%m-%d') if order.date_order else 'N/A',
            })
            
        values = {
            'employee': employee,
            'orders_data': orders_data,
            'search': search,
            'filterby': filterby or 'all',
            'total_orders': total_orders,
            'sales_value_str': sales_value_str,
            'conversion_rate_str': conversion_rate_str,
            'page_name': 'sale_orders',
        }
        return request.render("All_in_one_employee_portal.portal_my_sales", values)

    @http.route(['/my/sales/<int:order_id>'], type='http', auth="user", website=True)
    def portal_my_sale_detail(self, order_id, **kw):
        employee = request.env.user.employee_id
        if not employee:
            return request.redirect('/my')
            
        order = request.env['sale.order'].sudo().browse(order_id)
        if not order.exists() or order.user_id.id != request.env.user.id:
            return request.redirect('/my/sales')
            
        # Handle log note submission (POST)
        if http.request.httprequest.method == 'POST' and kw.get('action') == 'log_note':
            new_note = kw.get('new_note')
            if new_note:
                order.message_post(body=new_note, subtype_xmlid="mail.mt_note")
            return request.redirect(f'/my/sales/{order_id}?success_note=1')
            
        values = {
            'employee': employee,
            'order': order,
            'amount_total_str': '$ %.2f' % (order.amount_total or 0.0),
            'amount_untaxed_str': '$ %.2f' % (order.amount_untaxed or 0.0),
            'amount_tax_str': '$ %.2f' % (order.amount_tax or 0.0),
            'date_order_str': order.date_order.strftime('%Y-%m-%d %H:%M:%S') if order.date_order else 'N/A',
            'success_note': kw.get('success_note'),
            'page_name': 'sale_orders',
        }
        return request.render("All_in_one_employee_portal.portal_sale_detail", values)

    @http.route(['/my/announcements'], type='http', auth="user", website=True)
    def portal_my_announcements(self, **kw):
        employee = request.env.user.employee_id
        if not employee or not employee.portal_show_announcement:
            return request.redirect('/my')
            
        announcements = request.env['portal.announcement'].sudo().get_active_announcements(employee.id)
        
        values = {
            'employee': employee,
            'announcements': announcements,
            'page_name': 'announcements',
        }
        return request.render("All_in_one_employee_portal.portal_my_announcements", values)

    @http.route(['/my/announcements/<int:announcement_id>'], type='http', auth="user", website=True)
    def portal_my_announcement_detail(self, announcement_id, **kw):
        employee = request.env.user.employee_id
        if not employee or not employee.portal_show_announcement:
            return request.redirect('/my')
            
        announcement = request.env['portal.announcement'].sudo().browse(announcement_id)
        if not announcement.exists() or not announcement.is_published:
            return request.redirect('/my/announcements')
            
        # Employee access check
        if not announcement.all_employees and employee not in announcement.employee_ids:
            return request.redirect('/my/announcements')
            
        # Mark announcement as read
        if employee and employee not in announcement.read_employee_ids:
            announcement.sudo().write({'read_employee_ids': [(4, employee.id)]})
            
        values = {
            'employee': employee,
            'announcement': announcement,
            'page_name': 'announcements',
        }
        return request.render("All_in_one_employee_portal.portal_my_announcement_detail", values)

