/** @odoo-module */

import { useService } from "@web/core/utils/hooks";
const { Component, useRef, onWillStart, onMounted, onWillUnmount, useState, onWillUpdateProps } = owl;
import { session } from "@web/session";

// Fungsi animasi nilai
function animateValue(element, start, end, duration) {
  let startTimestamp = null;
  const step = (timestamp) => {
    if (!startTimestamp) startTimestamp = timestamp;
    const progress = Math.min((timestamp - startTimestamp) / duration, 1);
    const value = Math.floor(progress * (end - start) + start);
    element.textContent = value.toLocaleString();
    if (progress < 1) {
      requestAnimationFrame(step);
    }
  };
  requestAnimationFrame(step);
}

export class GuruKpiCard extends Component {
  static props = {
    startDate: { type: String, optional: true },
    endDate: { type: String, optional: true },
  };

  setup() {
    this.orm = useService("orm");
    this.actionService = useService("action");
    this.loadingOverlayRef = useRef("loadingOverlay");

    // Gunakan useState agar reaktif
    this.state = useState({
      kpiData: [],
      startDate: this.props.startDate || null,
      endDate: this.props.endDate || null,
      isLoading: false,
    });

    this.countdownInterval = null;
    this.refreshInterval = null;
    this.countdownTime = 10;
    this.isCountingDown = false;

    // Tangkap perubahan props (dari parent component)
    onWillUpdateProps(async (nextProps) => {
      if (nextProps.startDate !== this.props.startDate || nextProps.endDate !== this.props.endDate) {
        this.state.startDate = nextProps.startDate || null;
        this.state.endDate = nextProps.endDate || null;
        await this.updateKpiData();
      }
    });

    onWillStart(async () => {
      // Set default: bulan ini jika tidak ada props
      if (!this.state.startDate || !this.state.endDate) {
        const today = new Date();
        const firstDay = new Date(today.getFullYear(), today.getMonth(), 1);
        const lastDay = new Date(today.getFullYear(), today.getMonth() + 1, 0);
        this.state.startDate = this.formatDate(firstDay);
        this.state.endDate = this.formatDate(lastDay);
      }
      await this.updateKpiData();
    });

    onMounted(() => {
      this.attachEventListeners();
      // Set default periode di UI
      const periodSelection = document.getElementById("periodSelection");
      if (periodSelection) {
        periodSelection.value = "thisMonth";
      }
    });

    onWillUnmount(() => {
      this.clearIntervals();
      if (this.loadingOverlay && document.body.contains(this.loadingOverlay)) {
        document.body.removeChild(this.loadingOverlay);
        this.loadingOverlay = null;
      }
    });
  }

  // Helper: Format Date ke YYYY-MM-DD
  formatDate(date) {
    return date.toISOString().split("T")[0];
  }

  // Loading Overlay
  showLoading() {
    if (!this.loadingOverlay) {
      this.loadingOverlay = document.createElement("div");
      this.loadingOverlay.innerHTML = `
                <div class="musyrif-loading-overlay" style="
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background: rgba(0, 0, 0, 0.3);
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    z-index: 9999;
                ">
                    <div class="loading-spinner">
                        <i class="fas fa-sync-alt fa-spin fa-3x text-white"></i>
                    </div>
                </div>`;
      document.body.appendChild(this.loadingOverlay);
    }
    this.loadingOverlay.style.display = "flex";
    this.state.isLoading = true;
  }

  hideLoading() {
    if (this.loadingOverlay) {
      this.loadingOverlay.style.display = "none";
    }
    this.state.isLoading = false;
  }

  // Countdown
  toggleCountdown() {
    if (this.isCountingDown) {
      this.clearIntervals();
      const countdown = document.getElementById("timerCountdown");
      const icon = document.getElementById("timerIcon");
      if (countdown) countdown.textContent = "";
      if (icon) icon.className = "fas fa-clock";
    } else {
      this.startCountdown();
      const icon = document.getElementById("timerIcon");
      if (icon) icon.className = "fas fa-stop";
    }
    this.isCountingDown = !this.isCountingDown;
  }

  clearIntervals() {
    if (this.countdownInterval) clearInterval(this.countdownInterval);
    if (this.refreshInterval) clearInterval(this.refreshInterval);
    this.countdownInterval = null;
    this.refreshInterval = null;
  }

  startCountdown() {
    this.countdownTime = 10;
    this.clearIntervals();

    this.updateCountdownDisplay();

    this.countdownInterval = setInterval(() => {
      this.countdownTime--;
      if (this.countdownTime < 0) {
        this.countdownTime = 10;
        this.refreshChart();
      }
      this.updateCountdownDisplay();
    }, 1000);
  }

  updateCountdownDisplay() {
    const el = document.getElementById("timerCountdown");
    if (el) el.textContent = this.countdownTime;
  }

  refreshChart() {
    console.log("🔁 Memperbarui data KPI...");
    this.updateKpiData();
  }

  async updateKpiData() {
    this.showLoading();
    try {
      const { startDate, endDate } = this.state;

      console.log("🔍 Filtering with:", { startDate, endDate });

      const domainAbsenSiswa = [["kehadiran", "!=", false]]; // Hindari null
      const domainAbsenTahfidz = [["kehadiran", "!=", false]];
      const domainAbsenTahsin = [["kehadiran", "!=", false]];
      const domainAbsenEkskul = [["kehadiran", "!=", false]];

      if (startDate) {
        // Coba ganti ke create_date jika tanggal tidak ada
        domainAbsenSiswa.push(["create_date", ">=", startDate + " 00:00:00"]);
        domainAbsenTahfidz.push(["create_date", ">=", startDate + " 00:00:00"]);
        domainAbsenTahsin.push(["create_date", ">=", startDate + " 00:00:00"]);
        domainAbsenEkskul.push(["create_date", ">=", startDate + " 00:00:00"]);
      }
      if (endDate) {
        domainAbsenSiswa.push(["create_date", "<=", endDate + " 23:59:59"]);
        domainAbsenTahfidz.push(["create_date", "<=", endDate + " 23:59:59"]);
        domainAbsenTahsin.push(["create_date", "<=", endDate + " 23:59:59"]);
        domainAbsenEkskul.push(["create_date", "<=", endDate + " 23:59:59"]);
      }

      // Debug: Tampilkan domain
      console.log("Domain Absen Siswa:", domainAbsenSiswa);


      const [absensiSantri = 0, absensiTahfidz = 0, absensiTahsin = 0] = await Promise.all([
        this.orm.call("cdn.absensi_siswa_lines", "search_count", [domainAbsenSiswa]).catch(e => {
          console.error("Error count absensi_siswa_lines:", e);
          return 0;
        }),
        this.orm.call("cdn.absen_tahfidz_quran_line", "search_count", [domainAbsenTahfidz]).catch(e => {
          console.error("Error count absen_tahfidz_quran_line:", e);
          return 0;
        }),
        this.orm.call("cdn.absen_tahsin_quran_line", "search_count", [domainAbsenTahsin]).catch(e => {
          console.error("Error count absen_tahsin_quran_line:", e);
          return 0;
        }),
      ]);
      const absensiEkskul = await this.orm.call(
        "cdn.absen_ekskul_line",
        "search_count",
        [domainAbsenEkskul]
      );

      console.log("✅ Hasil count:", { absensiSantri, absensiTahfidz, absensiTahsin, absensiEkskul });

      this.state.kpiData = [
        {
          name: "Absen Siswa",
          value: absensiSantri,
          icon: "fa-user-check",
          res_model: "cdn.absensi_siswa_lines",
          domain: domainAbsenSiswa,
        },
        {
          name: "Absen Tahfidz",
          value: absensiTahfidz,
          icon: "fa-quran",
          res_model: "cdn.absen_tahfidz_quran_line",
          domain: domainAbsenTahfidz,
        },
        {
          name: "Absen Tahsin",
          value: absensiTahsin,
          icon: "fa-book",
          res_model: "cdn.absen_tahsin_quran_line",
          domain: domainAbsenTahsin,
        },
        {
          name: "Absen Ekskul",
          value: absensiEkskul,
          icon: "fa-chalkboard-teacher",
          res_model: "cdn.absen_ekskul_line",
          domain: domainAbsenEkskul,
        },
      ];

      // Animasi
      this.state.kpiData.forEach((kpi, index) => {
        const el = document.querySelector(`.kpi-value-${index}`);
        if (el) {
          animateValue(el, 0, kpi.value, 1000);
        }
      });

    } catch (error) {
      console.error("❌ Error fetching KPI ", error);
      // Tetap tampilkan nilai jika sudah dihitung
    } finally {
      this.hideLoading();
    }
  }

  attachEventListeners() {
    // Listener untuk card KPI
    const kpiCards = document.querySelectorAll(".kpi-card");
    kpiCards.forEach((card) => {
      card.addEventListener("click", (evt) => this.handleKpiCardClick(evt));
    });

    // Timer Button
    const timerButton = document.getElementById("timerButton");
    if (timerButton) {
      timerButton.addEventListener("click", this.toggleCountdown.bind(this));
    }

    // Input Tanggal
    const startDateInput = document.getElementById("startDate");
    const endDateInput = document.getElementById("endDate");

    if (startDateInput && endDateInput) {
      const handleChange = () => {
        this.state.startDate = startDateInput.value || null;
        this.state.endDate = endDateInput.value || null;
        this.updateKpiData();
      };
      startDateInput.addEventListener("change", handleChange);
      endDateInput.addEventListener("change", handleChange);
    }

    // Pemilihan Periode
    const periodSelection = document.getElementById("periodSelection");
    if (periodSelection) {
      const handlePeriodChange = () => {
        const today = new Date();
        let start, end;

        switch (periodSelection.value) {
          case "today":
            start = new Date(today.setHours(0, 0, 0, 0));
            end = new Date(today.setHours(23, 59, 59, 999));
            break;
          case "yesterday":
            start = new Date(today);
            start.setDate(today.getDate() - 1);
            start.setHours(0, 0, 0, 0);
            end = new Date(start);
            end.setHours(23, 59, 59, 999);
            break;
          case "thisWeek":
            start = new Date(today);
            start.setDate(today.getDate() - today.getDay());
            start.setHours(0, 0, 0, 0);
            end = new Date(start);
            end.setDate(start.getDate() + 6);
            end.setHours(23, 59, 59, 999);
            break;
          case "lastWeek":
            start = new Date(today);
            start.setDate(today.getDate() - today.getDay() - 7);
            start.setHours(0, 0, 0, 0);
            end = new Date(start);
            end.setDate(start.getDate() + 6);
            end.setHours(23, 59, 59, 999);
            break;
          case "thisMonth":
            start = new Date(today.getFullYear(), today.getMonth(), 1);
            end = new Date(today.getFullYear(), today.getMonth() + 1, 0);
            end.setHours(23, 59, 59, 999);
            break;
          case "lastMonth":
            start = new Date(today.getFullYear(), today.getMonth() - 1, 1);
            end = new Date(today.getFullYear(), today.getMonth(), 0);
            end.setHours(23, 59, 59, 999);
            break;
          case "thisYear":
            start = new Date(today.getFullYear(), 0, 1);
            end = new Date(today.getFullYear(), 11, 31);
            end.setHours(23, 59, 59, 999);
            break;
          case "lastYear":
            start = new Date(today.getFullYear() - 1, 0, 1);
            end = new Date(today.getFullYear() - 1, 11, 31);
            end.setHours(23, 59, 59, 999);
            break;
          default:
            start = new Date(today.getFullYear(), today.getMonth(), 1);
            end = new Date(today.getFullYear(), today.getMonth() + 1, 0);
            end.setHours(23, 59, 59, 999);
        }

        const formatDate = (date) => date.toISOString().split("T")[0];
        const formattedStart = formatDate(start);
        const formattedEnd = formatDate(end);

        this.state.startDate = formattedStart;
        this.state.endDate = formattedEnd;

        if (startDateInput && endDateInput) {
          startDateInput.value = formattedStart;
          endDateInput.value = formattedEnd;
        }

        this.updateKpiData();
      };

      periodSelection.addEventListener("change", handlePeriodChange);
      handlePeriodChange(); // Set default
    }
  }

  async handleKpiCardClick(evt) {
    this.clearIntervals();
    const timerIcon = document.getElementById("timerIcon");
    const timerCountdown = document.getElementById("timerCountdown");
    if (timerIcon) timerIcon.className = "fas fa-clock";
    if (timerCountdown) timerCountdown.textContent = "";

    const cardName = evt.currentTarget.dataset.name;
    const cardData = this.state.kpiData.find((kpi) => kpi.name === cardName);
    if (cardData) {
      await this.actionService.doAction({
        name: `${cardName} Details`,
        type: "ir.actions.act_window",
        res_model: cardData.res_model,
        views: [[false, "list"]],
        target: "current",
        domain: cardData.domain,
      });
    }
  }
}

GuruKpiCard.template = "owl.GuruKpiCard";