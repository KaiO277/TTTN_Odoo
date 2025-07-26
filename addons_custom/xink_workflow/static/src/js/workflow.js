import { Component, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class WorkflowClientAction extends Component {
    static template = "xink_workflow.workflow_template_backend";

    setup() {
        this.action = useService("action");
        this.module = this.props.action.context.module || "unknown";
        this.state = useState({
            workflow: {
                loading: true,
                error: null,
                name: "",
                mainflow: [],
                dependency: [],
                report: []
            }
        });
        this.loadWorkflow();
    }

    async loadWorkflow() {
        try {
            const response = await fetch(`/xink_workflow/get_workflow_data?module=${this.module}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const result = await response.json();
            
            // Handle workflow data properly whether it's a string or an object
            let workflowData;
            if (typeof result.data === 'string') {
                try {
                    workflowData = JSON.parse(result.data);
                } catch (e) {
                    workflowData = {};
                }
            } else {
                workflowData = result.data || {};
            }

            this.state.workflow = {
                loading: false,
                error: null,
                name: result.name || '',
                ...workflowData.workflow,
            };
        } catch (err) {
            console.error("Error loading workflow:", err);
            this.state.workflow = {
                loading: false,
                error: "Không tải được dữ liệu. " + err.message,
                name: "",
                mainflow: [],
                dependency: [],
                report: [],
            };
        }
    }

    async onNavigate(ev) {
        const url = ev.currentTarget?.dataset?.actionUrl;
        if (!url) return;
        const match = url.match(/action=([\w.]+)/);
        if (match) {
            await this.action.doAction(match[1]);
        } else {
            window.location.href = url;
        }
    }
}

registry.category("actions").add("xink_workflow.WorkflowClientAction", WorkflowClientAction);
