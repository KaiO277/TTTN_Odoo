/** @odoo-module **/

import { Dialog } from "@web/core/dialog/dialog";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";

patch(Dialog.prototype, {
    setup() {
        super.setup();
        if (this.props.title === "Odoo") {
            this.props.title = _t("Compose Email");
        }
    }
});
