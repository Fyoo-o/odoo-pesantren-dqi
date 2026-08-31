/** @odoo-module **/

import { FormController } from "@web/views/form/form_controller";
import { patch } from "@web/core/utils/patch";

patch(FormController.prototype, "pesantren_base.form_auto_new", {
    async saveButtonClicked(params = {}) {
        const notification = this.env.services.notification;
        let saved = false;

        try {
            saved = await this.save(params);
        } catch (error) {
            if (notification) {
                notification.add("Gagal Disimpan", {
                    type: "danger",
                    title: "Gagal",
                });
            }
            throw error;
        }

        if (saved) {
            if (notification) {
                notification.add("Berhasil Disimpan", {
                    type: "success",
                    title: "Berhasil",
                });
            }

            try {
                await this.createRecord();
            } catch (err) {
                console.warn("Auto-create record error after save:", err);
            }
        }

        return saved;
    }
});
