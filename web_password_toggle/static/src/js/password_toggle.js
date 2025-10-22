// File: static/src/js/password_toggle_widget.js
/** @odoo-module **/

import { registry } from "@web/core/registry";
import { CharField, charField } from "@web/views/fields/char/char_field";
import { useRef, useState } from "@odoo/owl";

export class PasswordToggleField extends CharField {
    static template = "cdn_orangtua.PasswordToggleField";

    setup() {
        super.setup();
        this.state = useState({
            showPassword: false
        });
        this.inputRef = useRef("input");
    }

    togglePasswordVisibility() {
        this.state.showPassword = !this.state.showPassword;
    }

    get inputType() {
        return this.state.showPassword ? "text" : "password";
    }
}

export const passwordToggleField = {
    ...charField,
    component: PasswordToggleField,
};

registry.category("fields").add("password_toggle", passwordToggleField);
