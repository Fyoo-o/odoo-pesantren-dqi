/** @odoo-module **/

import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { Component, useState, onWillUpdateProps, onWillDestroy } from "@odoo/owl";

export class PdfPreviewWidget extends Component {
    static template = "pesantren_guru.PdfPreviewWidget";
    static props = {
        ...standardFieldProps,
    };

    setup() {
        this.state = useState({
            pdfUrl: null,
            isLoading: true,
            hasError: false,
        });

        this.currentBlobUrl = null;
        this.updatePdfUrl(this.props.value);

        onWillUpdateProps((nextProps) => {
            if (nextProps.value !== this.props.value) {
                this.updatePdfUrl(nextProps.value);
            }
        });

        onWillDestroy(() => {
            this.revokeCurrentBlobUrl();
        });
    }

    revokeCurrentBlobUrl() {
        if (this.currentBlobUrl) {
            URL.revokeObjectURL(this.currentBlobUrl);
            this.currentBlobUrl = null;
        }
    }

    updatePdfUrl(value) {
        this.revokeCurrentBlobUrl();
        this.state.isLoading = true;
        this.state.hasError = false;

        if (!value) {
            this.state.pdfUrl = null;
            this.state.isLoading = false;
            return;
        }

        try {
            let base64Data = value;
            if (typeof value === "string" && value.includes(",")) {
                base64Data = value.split(",")[1];
            }

            const byteCharacters = atob(base64Data);
            const byteNumbers = new Array(byteCharacters.length);
            for (let i = 0; i < byteCharacters.length; i++) {
                byteNumbers[i] = byteCharacters.charCodeAt(i);
            }
            const byteArray = new Uint8Array(byteNumbers);
            const blob = new Blob([byteArray], { type: "application/pdf" });

            this.currentBlobUrl = URL.createObjectURL(blob);
            this.state.pdfUrl = `/web/static/lib/pdfjs/web/viewer.html?file=${encodeURIComponent(this.currentBlobUrl)}#page=1`;
        } catch (e) {
            console.error("Error creating Blob URL for PDF preview:", e);
            const resId = this.props.record.resId;
            if (resId) {
                const unique = Date.now();
                const contentUrl = `/web/content?model=${this.props.record.resModel}&id=${resId}&field=${this.props.name}&unique=${unique}`;
                this.state.pdfUrl = `/web/static/lib/pdfjs/web/viewer.html?file=${encodeURIComponent(contentUrl)}#page=1`;
            } else {
                this.state.hasError = true;
            }
        }

        setTimeout(() => {
            this.state.isLoading = false;
        }, 200);
    }

    onIframeLoad() {
        this.state.isLoading = false;
    }
}

export const pdfPreviewWidget = {
    component: PdfPreviewWidget,
    supportedTypes: ["binary"],
};

registry.category("fields").add("pdf_preview", pdfPreviewWidget);
