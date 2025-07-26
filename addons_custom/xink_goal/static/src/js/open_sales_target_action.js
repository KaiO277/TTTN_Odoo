odoo.define('xink_goal.OpenSalesTargetAction', function (require) {
    "use strict";
    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var OpenSalesTargetAction = AbstractAction.extend({
        start: function () {
            this.do_action('action_sales_target');
            return Promise.resolve();
        },
    });
    core.action_registry.add('xink_goal.OpenSalesTargetAction', OpenSalesTargetAction);
    return OpenSalesTargetAction;
});