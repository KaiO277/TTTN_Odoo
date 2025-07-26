odoo.define('product_custom.is_invoiceable_icon', function (require) {
    "use strict";
    var fieldRegistry = require('web.field_registry');
    var AbstractField = require('web.AbstractField');

    var IsInvoiceableIcon = AbstractField.extend({
        supportedFieldTypes: ['boolean'],
        template: 'product_custom.IsInvoiceableIcon',
        _render: function () {
            this.$el.empty();
            if (this.value) {
                this.$el.append('<i class="fa fa-check text-success" title="Có xuất hóa đơn"></i>');
            }
        },
    });

    fieldRegistry.add('is_invoiceable_icon', IsInvoiceableIcon);
}); 