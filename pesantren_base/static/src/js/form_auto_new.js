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

/**
 * Menyederhanakan Tombol Error Dialog Odoo ("Oh snap!") menjadi Single Tombol "Tutup"
 */
function customizeErrorDialogButtons() {
    const observer = new MutationObserver(() => {
        const dialogs = document.querySelectorAll(".modal-dialog, .o_dialog");
        dialogs.forEach((dialog) => {
            const footer = dialog.querySelector(".modal-footer");
            if (!footer) return;

            const buttons = footer.querySelectorAll("button");
            if (buttons.length >= 2) {
                let keepBtn = null;
                let discardBtn = null;

                buttons.forEach((btn) => {
                    const txt = (btn.textContent || "").trim().toLowerCase();
                    if (txt.includes("tunggu") || txt.includes("stay") || btn.classList.contains("btn-primary")) {
                        keepBtn = btn;
                    }
                    if (txt.includes("buang") || txt.includes("discard") || btn.classList.contains("btn-secondary")) {
                        discardBtn = btn;
                    }
                });

                if (keepBtn && discardBtn) {
                    // Sembunyikan tombol "Buang perubahan"
                    discardBtn.style.display = "none";
                    // Ubah teks tombol "Tunggu Di sini" menjadi "Tutup"
                    keepBtn.textContent = "Tutup";
                    keepBtn.classList.remove("btn-primary");
                    keepBtn.classList.add("btn-secondary", "dqi-custom-tutup-btn");
                }
            }
        });
    });

    observer.observe(document.body, { childList: true, subtree: true });
}

// Jalankan observer saat modul dimuat
if (typeof window !== "undefined" && !window._dqiDialogObserverBound) {
    window._dqiDialogObserverBound = true;
    customizeErrorDialogButtons();
}

patch(FormController.prototype, {
    async saveButtonClicked(params = {}) {
        let saved = false;

        try {
            saved = await super.saveButtonClicked(...arguments);
        } catch (error) {
            return false;
        }

        // Pastikan record benar-benar tersimpan dan tidak lagi dirty/baru
        const root = this.model?.root;
        const isSuccessfullySaved = saved && root && !root.isDirty && !root.isNew;

        if (isSuccessfullySaved) {
            // Popup Hijau Berhasil Disimpan
            await showCenterSavePopup(
                "success",
                "Berhasil Disimpan",
                "Form otomatis siap untuk data baru"
            );

            // Buka form baru yang kosong
            try {
                if (typeof this.createRecord === "function") {
                    await this.createRecord();
                } else if (typeof this.onClickCreate === "function") {
                    await this.onClickCreate();
                }
            } catch (err) {
                console.warn("Auto-create record error after save:", err);
            }
        }

        return saved;
    }
});
