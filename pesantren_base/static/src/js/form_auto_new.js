/** @odoo-module **/

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

        overlay.addEventListener("click", () => {
            clearTimeout(timer);
            closePopup();
        });
    });
}

/**
 * Customizer untuk Error Dialog ("Oh snap!") & Event Handler Simpan
 */
if (typeof window !== "undefined" && !window._dqiSaveHandlerBound) {
    window._dqiSaveHandlerBound = true;

    // Observer untuk mengubah judul Error Dialog & Tombolnya
    const setupObserver = () => {
        if (!document.body) return;

        const observer = new MutationObserver(() => {
            const dialogs = document.querySelectorAll(".modal-dialog, .o_dialog");
            dialogs.forEach((dialog) => {
                // Ubah Judul "Oh snap!" menjadi "Gagal Menyimpan"
                const titleEl = dialog.querySelector(".modal-title, .o_dialog_title, h4, h5, .modal-header h4, .modal-header h5");
                if (titleEl) {
                    const titleText = (titleEl.textContent || "").trim().toLowerCase();
                    if (titleText.includes("oh snap") || titleText.includes("snap")) {
                        titleEl.textContent = "Gagal Menyimpan";
                    }
                }

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
    };

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", setupObserver);
    } else {
        setupObserver();
    }

    // Event listener saat tombol Simpan diklik
    document.addEventListener("click", (ev) => {
        const btn = ev.target?.closest ? ev.target.closest("button.o_form_button_save, .o_form_status_indicator button.o_form_button_save, button[name='action_save']") : null;
        if (!btn) return;

        // Ambil elemen form saat ini
        const formEl = btn.closest(".o_form_view");
        if (!formEl) return;

        // Pantau kapan proses simpan selesai di Odoo
        setTimeout(async () => {
            // Cek apakah ada dialog error yang muncul
            const hasErrorDialog = document.querySelector(".modal-dialog, .o_dialog");
            if (hasErrorDialog) {
                // Ada error, jangan tampilkan popup sukses
                return;
            }

            // Jika tidak ada error, tampilkan popup sukses hijau
            await showCenterSavePopup(
                "success",
                "Berhasil Disimpan",
                "Form otomatis siap untuk data baru"
            );

            // Cari dan klik tombol "Baru" untuk otomatis membuka form baru yang kosong
            const createBtn = document.querySelector("button.o_form_button_create");
            if (createBtn) {
                createBtn.click();
            }
        }, 600);
    });
}
