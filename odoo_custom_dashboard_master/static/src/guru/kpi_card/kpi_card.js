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

    onWillUpdateProps(async (nextProps) => {
      if (nextProps.startDate !== this.props.startDate || nextProps.endDate !== this.props.endDate) {
        this.state.startDate = nextProps.startDate || null;
        this.state.endDate = nextProps.endDate || null;
        await this.updateKpiData();
      }
    });

    onWillStart(async () => {
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

  formatDate(date) {
    return date.toISOString().split("T")[0];
  }

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

  clearIntervals() {
    if (this.countdownInterval) clearInterval(this.countdownInterval);
    if (this.refreshInterval) clearInterval(this.refreshInterval);
    this.countdownInterval = null;
    this.refreshInterval = null;
  }

  async updateKpiData() {
    this.showLoading();
    try {
      const { startDate, endDate } = this.state;

      // DOMAIN UNTUK SETIAP MODEL
      const domainAbsenSiswa = [["kehadiran", "!=", false]];
      const domainAbsenHalaqoh = [["kehadiran", "!=", false]];
      const domainAbsenEkskul = [["kehadiran", "!=", false]];

      if (startDate) {
        domainAbsenSiswa.push(["create_date", ">=", startDate + " 00:00:00"]);
        domainAbsenHalaqoh.push(["create_date", ">=", startDate + " 00:00:00"]);
        domainAbsenEkskul.push(["create_date", ">=", startDate + " 00:00:00"]);
      }
      if (endDate) {
        domainAbsenSiswa.push(["create_date", "<=", endDate + " 23:59:59"]);
        domainAbsenHalaqoh.push(["create_date", "<=", endDate + " 23:59:59"]);
        domainAbsenEkskul.push(["create_date", "<=", endDate + " 23:59:59"]);
      }

      // PEMANGGILAN ORM
      let absensiSiswa = [],
        absensiHalaqoh = [],
        absensiEkskul = [];

      try {
        absensiSiswa = await this.orm.call(
          "cdn.absensi_siswa_lines",
          "search_read",
          [domainAbsenSiswa, ["id", "siswa_id", "kehadiran", "create_date"]],
          { context: this.env.context }
        );
      } catch (e) {
        console.error("Error absensi_siswa_lines:", e);
      }

      try {
        absensiHalaqoh = await this.orm.call(
          "cdn.absen_halaqoh_line",
          "search_read",
          [domainAbsenHalaqoh, ["id", "siswa_id", "kehadiran", "create_date"]],
          { context: this.env.context }
        );
      } catch (e) {
        console.error("Error absen_halaqoh_line:", e);
      }

      try {
        absensiEkskul = await this.orm.call(
          "cdn.absen_ekskul_line",
          "search_read",
          [domainAbsenEkskul, ["id", "siswa_id", "kehadiran", "create_date"]],
          { context: this.env.context }
        );
      } catch (e) {
        console.error("Error absen_ekskul_line:", e);
      }

      // HITUNG TOTAL
      const totalAbsenSiswa = absensiSiswa?.length || 0;
      const totalAbsenHalaqoh = absensiHalaqoh?.length || 0;
      const totalAbsenEkskul = absensiEkskul?.length || 0;

      // SET STATE KPI
      this.state.kpiData = [
        {
          name: "Absen Siswa",
          value: totalAbsenSiswa,
          icon: "fa-user-check",
          res_model: "cdn.absensi_siswa_lines",
          domain: domainAbsenSiswa,
        },
        {
          name: "Absen Halaqoh",
          value: totalAbsenHalaqoh,
          icon: "fa-quran",
          res_model: "cdn.absen_halaqoh_line",
          domain: domainAbsenHalaqoh,
        },
        {
          name: "Absen Ekskul",
          value: totalAbsenEkskul,
          icon: "fa-chalkboard-teacher",
          res_model: "cdn.absen_ekskul_line",
          domain: domainAbsenEkskul,
        },
      ];

      // ANIMASI NILAI
      this.state.kpiData.forEach((kpi, index) => {
        const el = document.querySelector(`.kpi-value-${index}`);
        if (el) {
          animateValue(el, 0, kpi.value, 1000);
        }
      });
    } catch (error) {
      console.error("❌ Error fetching KPI ", error);
    } finally {
      this.hideLoading();
    }
  }

  attachEventListeners() {
    const kpiCards = document.querySelectorAll(".kpi-card");
    kpiCards.forEach((card) => {
      card.addEventListener("click", (evt) => this.handleKpiCardClick(evt));
    });

    const periodSelection = document.getElementById("periodSelection");
    if (periodSelection) {
      periodSelection.addEventListener("change", () => this.updateKpiData());
    }
  }

  async handleKpiCardClick(evt) {
    const cardName = evt.currentTarget.dataset.name;
    const cardData = this.state.kpiData.find((kpi) => kpi.name === cardName);
    if (cardData) {
      await this.actionService.doAction({
        name: `${cardName} Details`,
        type: "ir.actions.act_window",
        res_model: cardData.res_model,
        views: [[false, "list"], [false, "form"]],
        target: "current",
        domain: cardData.domain,
      });
    }
  }
}

GuruKpiCard.template = "owl.GuruKpiCard";
