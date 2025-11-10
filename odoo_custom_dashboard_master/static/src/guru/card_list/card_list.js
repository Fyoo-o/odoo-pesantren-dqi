/** @odoo-module **/
import { Component, onWillStart, onMounted, onWillUnmount } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class BaseDateFilteredListComponent extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        const today = new Date();

        // Inisialisasi state dasar
        this.state = {
            items: [],
            startDate: this.getDefaultStartDate(today),
            endDate: this.getDefaultEndDate(today),
        };

        this.countdownInterval = null;
        this.countdownTime = 10;
        this.isCountingDown = false;

        onWillStart(async () => {
            await this.fetchData();
        });

        onMounted(() => {
            this.attachEventListeners();
        });

        onWillUnmount(() => {
            if (this.countdownInterval) {
                clearInterval(this.countdownInterval);
                this.countdownInterval = null;
            }
        });
    }

    // ——— TANGGAL DEFAULT ———
    getDefaultStartDate(today) {
        return new Date(Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), 1, 0, 0, 1))
            .toISOString()
            .split("T")[0];
    }

    getDefaultEndDate(today) {
        return new Date(
            Date.UTC(
                today.getUTCFullYear(),
                today.getUTCMonth(),
                today.getUTCDate(),
                23,
                59,
                59,
                999
            )
        )
            .toISOString()
            .split("T")[0];
    }

    // ——— TIMER ———
    toggleCountdown() {
        if (this.isCountingDown) {
            this.clearIntervals();
            this.updateCountdownDisplay("");
            this.updateTimerIcon(true);
        } else {
            this.isCountingDown = true;
            this.startCountdown();
            this.updateTimerIcon(false);
        }
    }

    clearIntervals() {
        if (this.countdownInterval) {
            clearInterval(this.countdownInterval);
            this.countdownInterval = null;
        }
        this.countdownTime = 10;
        this.isCountingDown = false;
    }

    startCountdown() {
        this.countdownTime = 10;
        this.clearIntervals();
        this.updateCountdownDisplay(this.countdownTime);

        this.countdownInterval = setInterval(() => {
            this.countdownTime--;
            if (this.countdownTime < 0) {
                this.countdownTime = 10;
                this.fetchData();
            }
            this.updateCountdownDisplay(this.countdownTime);
        }, 1000);

        this.isCountingDown = true;
    }

    updateCountdownDisplay(text) {
        const el = document.getElementById("timerCountdown");
        if (el) el.textContent = text;
    }

    updateTimerIcon(showClock) {
        const icon = document.getElementById("timerIcon");
        if (!icon) return;
        icon.classList.toggle("fas", showClock);
        icon.classList.toggle("fa-clock", showClock);
    }

    // ——— EVENT LISTENERS ———
    attachEventListeners() {
        const startDateInput = document.getElementById("startDate");
        const endDateInput = document.getElementById("endDate");
        const timerButton = document.getElementById("timerButton");
        const periodSelection = document.getElementById("periodSelection");

        // Timer button
        if (timerButton) {
            timerButton.addEventListener("click", this.toggleCountdown.bind(this));
        }

        // Date inputs
        if (startDateInput) {
            startDateInput.addEventListener("change", (e) => {
                this.state.startDate = e.target.value;
                this.fetchData();
            });
        }
        if (endDateInput) {
            endDateInput.addEventListener("change", (e) => {
                this.state.endDate = e.target.value;
                this.fetchData();
            });
        }

        // Period dropdown
        if (periodSelection) {
            periodSelection.addEventListener("change", () => {
                const today = new Date();
                let startDate, endDate;

                switch (periodSelection.value) {
                    case "today":
                        startDate = new Date(Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), today.getUTCDate(), 0, 0, 0, 1));
                        endDate = new Date(Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), today.getUTCDate(), 23, 59, 59, 999));
                        break;
                    case "yesterday":
                        startDate = new Date(Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), today.getUTCDate() - 1, 0, 0, 0, 1));
                        endDate = new Date(Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), today.getUTCDate() - 1, 23, 59, 59, 999));
                        break;
                    case "thisWeek":
                        const startOfWeek = today.getUTCDate() - today.getUTCDay();
                        startDate = new Date(Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), startOfWeek, 0, 0, 0, 1));
                        endDate = new Date(Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), startOfWeek + 6, 23, 59, 59, 999));
                        break;
                    case "lastWeek":
                        const lastWeekStart = today.getUTCDate() - today.getUTCDay() - 7;
                        startDate = new Date(Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), lastWeekStart, 0, 0, 0, 1));
                        endDate = new Date(Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), lastWeekStart + 6, 23, 59, 59, 999));
                        break;
                    case "thisMonth":
                        startDate = new Date(Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), 1, 0, 0, 0, 1));
                        endDate = new Date(Date.UTC(today.getUTCFullYear(), today.getUTCMonth() + 1, 0, 23, 59, 59, 999));
                        break;
                    case "lastMonth":
                        startDate = new Date(Date.UTC(today.getUTCFullYear(), today.getUTCMonth() - 1, 1, 0, 0, 0, 1));
                        endDate = new Date(Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), 0, 23, 59, 59, 999));
                        break;
                    case "thisYear":
                        startDate = new Date(Date.UTC(today.getUTCFullYear(), 0, 1, 0, 0, 0, 1));
                        endDate = new Date(Date.UTC(today.getUTCFullYear(), 11, 31, 23, 59, 59, 999));
                        break;
                    case "lastYear":
                        startDate = new Date(Date.UTC(today.getUTCFullYear() - 1, 0, 1, 0, 0, 0, 1));
                        endDate = new Date(Date.UTC(today.getUTCFullYear() - 1, 11, 31, 23, 59, 59, 999));
                        break;
                    default:
                        // Default: this month
                        startDate = new Date(Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), 1, 0, 0, 0, 1));
                        endDate = new Date(Date.UTC(today.getUTCFullYear(), today.getUTCMonth() + 1, 0, 23, 59, 59, 999));
                }

                if (startDate && endDate) {
                    this.state.startDate = startDate.toISOString().split("T")[0];
                    this.state.endDate = endDate.toISOString().split("T")[0];
                    if (startDateInput) startDateInput.value = this.state.startDate;
                    if (endDateInput) endDateInput.value = this.state.endDate;
                    this.fetchData();
                }
            });
        }
    }

    // ——— METODE ABSTRAK ———
    // Harus di-override oleh subclass
    async fetchData() {
        throw new Error("fetchData() must be implemented in subclass");
    }

    onRowClick(record) {
        // Opsional: override jika perlu navigasi
    }
}
/** @odoo-module **/
export class GuruList extends BaseDateFilteredListComponent {
    async fetchData() {
        try {
            this.state.isLoading = true;

            // Filter
            const domain = [['penilaian_id.state', '=', 'done']];
            if (this.state.startDate) domain.push(['penilaian_id.tanggal', '>=', this.state.startDate]);
            if (this.state.endDate) domain.push(['penilaian_id.tanggal', '<=', this.state.endDate]);

            let lineRecords = [],
            penilaianRecords = [];

            // 1️⃣ Ambil semua line penilaian
            try {
                lineRecords = await this.orm.searchRead(
                    "cdn.penilaian_quran_line",
                    domain,
                    ["id", "penilaian_id", "jml_baris"],
                    {
                        context: {
                        ...this.env.context,
                        from_guru_quran: true,
                        },
                    }
                );
            } catch (e) {
                console.error("Error penilaian_quran_lines:", e);
            }
            
            console.log("Jumlah line ditemukan:", lineRecords.length);

            if (!lineRecords.length) {
                this.state.items = [];
                await this.render();
                return;
            }

            // 2️⃣ Ambil semua penilaian terkait untuk tahu siswa & halaqoh
            const penilaianIds = [...new Set(lineRecords.map(l => l.penilaian_id?.[0]).filter(Boolean))];
            try {
                penilaianRecords = await this.orm.searchRead(
                    "cdn.penilaian_quran",
                    [["id", "in", penilaianIds]],
                    ["id", "siswa_id", "halaqoh_id"],
                    {
                        context: {
                        ...this.env.context,
                        from_guru_quran: true,
                        },
                    }
                );
            } catch (e) {
                console.error("Error penilaian_quran:", e);
            }

            const penilaianMap = new Map(penilaianRecords.map(p => [
                p.id,
                {
                    siswa: p.siswa_id ? p.siswa_id[1] : 'N/A',
                    halaqoh: p.halaqoh_id ? p.halaqoh_id[1] : 'N/A',
                }
            ]));

            // 3️⃣ Agregasi total baris per siswa
            const totalPerSiswa = {};
            for (const line of lineRecords) {
                const penilaianId = line.penilaian_id?.[0];
                const info = penilaianMap.get(penilaianId);
                if (!info) continue;

                if (!totalPerSiswa[info.siswa]) {
                    totalPerSiswa[info.siswa] = {
                        nama: info.siswa,
                        halaqoh: info.halaqoh,
                        total_baris: 0,
                        penilaian_id: penilaianId,
                    };
                }
                totalPerSiswa[info.siswa].total_baris += line.jml_baris || 0;
            }

            // 4️⃣ Urutkan dan tampilkan top 10
            const sorted = Object.values(totalPerSiswa)
                .sort((a, b) => b.total_baris - a.total_baris)
                .slice(0, 10);

            this.state.items = sorted.map((item, index) => ({
            id: item.penilaian_id, // tambahkan ini
            number: index + 1,
            nama: item.nama,
            halaqoh: item.halaqoh,
            baris: item.total_baris,
            }));

            this.state.hasData = this.state.items.length > 0;
            await this.render();
        } catch (error) {
            console.error("Error fetching Top Hafalan data (GuruList):", error);
            this.state.items = [];
            await this.render();
        } finally {
            this.state.isLoading = false;
        }
    }

    openRecord(penilaianId) {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Detail Penilaian",
            res_model: "cdn.penilaian_quran",
            res_id: penilaianId,
            views: [[false, "form"]],
            target: "current",
        });
    }
}

GuruList.template = "owl.GuruList";

export class EkskulList extends BaseDateFilteredListComponent {
    async fetchData() {
        try {
            const domain = [];
            if (this.state.startDate) domain.push(["tanggal", ">=", this.state.startDate]);
            if (this.state.endDate) domain.push(["tanggal", "<=", this.state.endDate]);

            const records = await this.orm.searchRead(
                "cdn.absen_ekskul_line",
                domain,
                ["id", "siswa_id", "guru", "ekskul", "kehadiran", "tanggal"]
            );

            this.state.items = this.processEkskulData(records);
            await this.render();
        } catch (error) {
            console.error("Error fetching Ekskul data:", error);
        }
    }

    processEkskulData(data) {
        return data.map((rec, i) => ({
            number: i + 1,
            id: rec.id,
            nama: Array.isArray(rec.siswa_id) ? rec.siswa_id[1] : "N/A",
            ekskul: Array.isArray(rec.ekskul) ? rec.ekskul[1] : "N/A",
            pembimbing: Array.isArray(rec.guru) ? rec.guru[1] : "N/A",
            kehadiran: rec.kehadiran || "N/A",
            onClick: () => this.openRecord(rec.id)
        }));
    }

    openRecord(id) {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Kehadiran Ekskul",
            res_model: "cdn.absen_ekskul_line",
            res_id: id,
            views: [[false, "form"]],
            target: "current",
        });
    }
}

EkskulList.template = "owl.EkskulList";