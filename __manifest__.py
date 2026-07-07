{
    'name': 'All-in-One Employee Portal | Employee Portal | ESS | Employee Self-Service Portal',
    
    'summary': 'Employee Self-Service (ESS) Portal with a modern dashboard - Attendance, Profile, CRM, Sales, Leaves, Timesheets, Payroll, Expenses, Tasks, and Shifts.',
    
    'description': '''
        A comprehensive Employee Self-Service (ESS) portal for Odoo that allows employees to manage all their daily operations through a unified, beautiful, mobile-responsive dashboard using a single Odoo Portal license.
        
        Features:
        • Save money on expensive Odoo internal user licenses - manage all employees via portal accounts
        • Granular access control - enable or disable dashboard tiles for each employee from the Odoo backend
        • Employee Profile - view and update personal contact details, address, and profile photo
        • One-click Attendance - check-in and check-out with automatic GPS coordinate tracking
        • CRM Opportunity Sync - view, track, and update sales leads/opportunities with live chatter log
        • Sales Quotations & Orders - list assigned quotes/sales orders and follow status changes
        • Task Management - view assigned work tasks, project descriptions, and deadlines
        • Timesheets Logging - log and track work hours directly from the front-end portal
        • Time Off & Leaves - check balances and submit leave requests for manager approval
        • Payroll integration - securely download salary payslips as PDF files
        • Expenses Submission - log costs and upload receipts for reimbursements
        • Work Planning - view shift calendars and weekly planning schedules
        
        Perfect for businesses looking to streamline HR operations and minimize Odoo license fees.
        
        Configuration:
        • Simple checkbox activation on the Employee profile settings tab
        • Automatic portal user creation and link on employee save
        • Checkbox list to toggle visibility for each of the 10 portal dashboard tiles
    ''',
    
    'author': 'Eazecode',
    'support': 'eazecode@gmail.com',
    
    'price': 120.00,
    'currency': 'USD',
    
    'version': '18.0.1.0.0',
    'license': 'OPL-1',
    'category': 'Human Resources',
    
    'depends': [
        'portal', 
        'hr', 
        'hr_attendance', 
        'hr_holidays', 
        'hr_payroll', 
        'project', 
        'hr_timesheet', 
        'hr_expense', 
        'planning', 
        'crm', 
        'sale',
    ],
    
    'data': [
        'security/ir.model.access.csv',
        'security/security_rules.xml',
        'security/ir_rule.xml',
        'views/portal_templates.xml',
        'views/profile_templates.xml',
        'views/hr_employee_views.xml',
        'views/hr_attendance_views.xml',
        'views/project_task_views.xml',
        'views/announcement_views.xml',
    ],
    
    'assets': {
        'web.assets_frontend': [
            'All_in_one_employee_portal/static/src/css/portal_dashboard.css',
            'All_in_one_employee_portal/static/src/js/portal_attendance.js',
        ],
    },
    
    'images': [
        'static/description/banner.png',
        'static/description/icon.png',
    ],
    
    'installable': True,
    'application': True,
    'auto_install': False,
}
