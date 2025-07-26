# Copyright 2019 Marcelo Frare (Ass. PNLUG - Gruppo Odoo <http://odoo.pnlug.it>)
# Copyright 2019 Stefano Consolaro (Ass. PNLUG - Gruppo Odoo <http://odoo.pnlug.it>)

{
    "name": "Management System - Nonconformity Product",
    "summary": "Bridge module between Product and Management System.",
    "version": "18.0.1.0.0",
    "category": "Xink OCA Management System",
    "license": "AGPL-3",
    "author": "Associazione PNLUG - Gruppo Odoo, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/management-system",
    "development_status": "Beta",
    "depends": ["product", "mgmtsystem_nonconformity"],
    "data": ["views/mgmtsystem_nonconformity_views.xml"],
    "installable": True,
}
