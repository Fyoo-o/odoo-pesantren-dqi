/** @odoo-module **/

import { registry } from "@web/core/registry";
import { url } from "@web/core/utils/urls";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { Component, useState, onWillUpdateProps, onWillDestroy } from "@odoo/owl";

export class PdfPreviewWidget extends Component {
    static template = "pesantren_guru.PdfPreviewWidget";
    static props = {
        ...standardFieldProps,
    };

    setup() {
        this.state = useState({
            isLoading: true,
            hasError: false,
        });

        this._blobUrl = null;
        this._viewerUrl = null;

        this._buildUrl();

        onWillUpdateProps((nextProps) => {
            const curHasData = !!this.props.record.data[this.props.name];
            const nextHasData = !!nextProps.record.data[nextProps.name];
            const curId = this.props.record.resId;
            const nextId = nextProps.record.resId;

            if (curHasData !== nextHasData || curId !== nextId) {
                this._buildUrl(nextProps);
            }
        });

        onWillDestroy(() => {
            this._revokeBlobUrl();
        });
    }

    _revokeBlobUrl() {
        if (this._blobUrl) {
            URL.revokeObjectURL(this._blobUrl);
            this._blobUrl = null;
        }
    }

    _buildUrl(props) {
        props = props || this.props;
        this._revokeBlobUrl();

        this.state.isLoading = true;
        this.state.hasError = false;

        const value = props.record.data[props.name];
        if (!value) {
            this._viewerUrl = null;
            this.state.isLoading = false;
            return;
        }

        const resId = props.record.resId;

        if (resId) {
            const unique = Date.now();
            const contentUrl = url("/web/content", {
                model: props.record.resModel,
                field: props.name,
                id: resId,
                unique: unique,
            });
            this._viewerUrl = `/web/static/lib/pdfjs/web/viewer.html?file=${encodeURIComponent(contentUrl)}#page=1`;
        } else {
            this._viewerUrl = null;
            this.state.isLoading = false;
        }
    }

    get viewerUrl() {
        return this._viewerUrl;
    }

    onIframeLoad() {
        this.state.isLoading = false;
    }

    onIframeError() {
        this.state.isLoading = false;
        this.state.hasError = true;
    }
}

export const pdfPreviewWidget = {
    component: PdfPreviewWidget,
    supportedTypes: ["binary"],
};

registry.category("fields").add("pdf_preview", pdfPreviewWidget);
