/** @odoo-module **/

import { FormController } from "@web/views/form/form_controller";
import { patch } from "@web/core/utils/patch";

/**
 * Menampilkan Pop-Up Modal di Tengah Layar (Center Popup Modal)
 * @param {'success'|'danger'} type
 * @param {string} title
 * @param {string} subtitle
 * @returns {Promise<void>}
 */
function showCenterSavePopup(type, title, subtitle = "") {
    return new Promise((resolve) => {
        // Hapus popup sebelumnya jika masih ada di DOM
        const existing = document.querySelector(".dqi-save-popup-overlay");
        if (existing) {
            existing.remove();
        }

        const isSuccess = type === "success";
        const iconSvg = isSuccess
            ? `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>`
            : `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>`;

        const overlay = document.createElement("div");
        overlay.className = "dqi-save-popup-overlay";
        overlay.innerHTML = `
            <div class="dqi-save-popup-card">
                <div class="dqi-popup-icon-wrapper ${type}">
                    ${iconSvg}
                </div>
                <h4 class="dqi-popup-title">${title}</h4>
                ${subtitle ? `<p class="dqi-popup-subtitle">${subtitle}</p>` : ""}
            </div>
        `;

        document.body.appendChild(overlay);

        const closePopup = () => {
            overlay.classList.add("dqi-hiding");
            setTimeout(() => {
                if (overlay.parentNode) {
                    overlay.parentNode.removeChild(overlay);
                }
                resolve();
            }, 200);
        };

        // Tutup otomatis setelah 1.4 detik
        const timer = setTimeout(closePopup, 1400);

        // Pengguna bisa klik area luar untuk langsung menutup
        overlay.addEventListener("click", () => {
            clearTimeout(timer);
            closePopup();
        });
    });
}

patch(FormController.prototype, {
    async saveButtonClicked(params = {}) {
        let saved = false;

        try {
            saved = await super.saveButtonClicked(...arguments);
        } catch (error) {
            showCenterSavePopup(
                "danger",
                "Gagal Disimpan",
                "Mohon periksa kembali kelengkapan data"
            );
            throw error;
        }

        if (saved) {
            await showCenterSavePopup(
                "success",
                "Berhasil Disimpan",
                "Form otomatis siap untuk data baru"
            );

            try {
                await this.createRecord();
            } catch (err) {
                console.warn("Auto-create record error after save:", err);
            }
        }

        return saved;
    }
});
