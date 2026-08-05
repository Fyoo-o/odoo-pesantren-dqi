/** @odoo-module **/

if (typeof window !== "undefined" && !window._penilaianLiveLabelBound) {
    window._penilaianLiveLabelBound = true;

    document.addEventListener("input", (ev) => {
        try {
            const target = ev.target;
            if (!target) return;

            // Cek apakah user sedang mengetik di field tipe_label
            const isTipeLabel =
                target.name === "tipe_label" ||
                target.closest('[name="tipe_label"]') ||
                (target.id && target.id.includes("tipe_label"));

            if (isTipeLabel) {
                const formEl = target.closest(".o_form_view");
                if (!formEl) return;

                const textValue = (target.value || "").trim();

                // Cari fallback dari dropdown / input field 'tipe'
                const tipeField = formEl.querySelector('[name="tipe"] select, [name="tipe"] input');
                let fallbackVal = "";
                if (tipeField) {
                    if (tipeField.tagName === "SELECT") {
                        fallbackVal = tipeField.options[tipeField.selectedIndex]?.text || "";
                    } else {
                        fallbackVal = tipeField.value || "";
                    }
                }

                const finalText = textValue || fallbackVal || "Penilaian";

                // Cari seluruh baris di tabel penilaian_ids
                const rows = formEl.querySelectorAll('[name="penilaian_ids"] tr.o_data_row, [name="penilaian_ids"] tbody tr');
                rows.forEach((row) => {
                    const cell =
                        row.querySelector('[data-name="name"]') ||
                        row.querySelector('[name="name"]') ||
                        row.querySelector("td.o_data_cell") ||
                        row.cells[0];

                    if (cell) {
                        const inputNode = cell.querySelector("input");
                        if (inputNode) {
                            inputNode.value = finalText;
                        } else {
                            cell.textContent = finalText;
                        }
                    }
                });
            }
        } catch (err) {
            console.warn("Live label input error:", err);
        }
    });
}
