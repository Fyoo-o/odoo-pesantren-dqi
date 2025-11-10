/** @odoo-module */
import { registry } from "@web/core/registry";
import { GuruKpiCard } from "./kpi_card/kpi_card";
import { GuruChartRenderer } from "./chart_renderer/chart_renderer";
import { EkskulList, GuruList } from "./card_list/card_list";
import { useState, Component, onMounted, onWillUnmount } from "@odoo/owl";

export class OwlGuruDashboard extends Component {
  setup() {
    this.state = useState({
      showDatePicker: false,
      selectedDateRange: null,
      tempDateRange: { start: "", end: "" },
      selectedPeriod: "thisMonth", // default
    });

    // Listener klik di luar popup
    this._handleClickOutside = (ev) => {
      const popup = document.getElementById("datePickerContainer");
      const button = document.getElementById("datePickerButton");

      if (popup && button && !popup.contains(ev.target) && !button.contains(ev.target)) {
        this.state.showDatePicker = false;
      }
    };

    onMounted(() => {
      document.addEventListener("click", this._handleClickOutside);
      this.setPeriod(this.state.selectedPeriod); // set default saat load
    });

    onWillUnmount(() => {
      document.removeEventListener("click", this._handleClickOutside);
    });
  }

  toggleDatePicker() {
    this.state.showDatePicker = !this.state.showDatePicker;
    if (this.state.showDatePicker && this.state.selectedDateRange) {
      this.state.tempDateRange = { ...this.state.selectedDateRange };
    }
  }

  applyDateRange() {
    if (this.state.tempDateRange.start && this.state.tempDateRange.end) {
      this.state.selectedDateRange = { ...this.state.tempDateRange };
      this.state.selectedPeriod = "custom"; // otomatis ke custom
      this.state.showDatePicker = false;
    }
  }

  formatDate(dateString) {
    if (!dateString) return "";
    const date = new Date(dateString);
    const day = String(date.getDate()).padStart(2, "0");
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const year = date.getFullYear();
    return `${year}-${month}-${day}`;
  }

  // Format rentang tanggal untuk tombol
  formatDateRange() {
    if (this.state.selectedDateRange && this.state.selectedDateRange.start && this.state.selectedDateRange.end) {
      const start = new Date(this.state.selectedDateRange.start).toLocaleDateString("id-ID", {
        day: "numeric",
        month: "short",
        year: "numeric",
      });
      const end = new Date(this.state.selectedDateRange.end).toLocaleDateString("id-ID", {
        day: "numeric",
        month: "short",
        year: "numeric",
      });
      return `${start} - ${end}`;
    }
    // Jika tidak ada custom range, tampilkan label periode
    return this.getPeriodLabel(this.state.selectedPeriod);
  }

  // Label periode untuk dropdown & fallback
  getPeriodLabel(period) {
    const labels = {
      today: "Hari Ini",
      yesterday: "Kemarin",
      thisWeek: "Minggu Ini",
      lastWeek: "Minggu Lalu",
      thisMonth: "Bulan Ini",
      lastMonth: "Bulan Lalu",
      thisYear: "Tahun Ini",
      lastYear: "Tahun Lalu",
      custom: "Rentang Tanggal",
    };
    return labels[period] || "Pilih Periode";
  }

  isPeriodSelected(period) {
    return this.state.selectedPeriod === period;
  }

  setPeriod(period) {
    const now = new Date();
    let start, end;

    // Jangan ubah jika sudah custom dan date range ada
    if (period === "custom" && this.state.selectedDateRange) {
      this.state.selectedPeriod = "custom";
      return;
    }

    switch (period) {
      case "today":
        start = end = now;
        break;
      case "yesterday":
        start = end = new Date(now.getFullYear(), now.getMonth(), now.getDate() - 1);
        break;
      case "thisWeek":
        start = new Date(now.getFullYear(), now.getMonth(), now.getDate() - now.getDay());
        end = new Date(start);
        end.setDate(start.getDate() + 6);
        break;
      case "lastWeek":
        start = new Date(now.getFullYear(), now.getMonth(), now.getDate() - now.getDay() - 7);
        end = new Date(start);
        end.setDate(start.getDate() + 6);
        break;
      case "thisMonth":
        start = new Date(now.getFullYear(), now.getMonth(), 1);
        end = new Date(now.getFullYear(), now.getMonth() + 1, 0);
        break;
      case "lastMonth":
        start = new Date(now.getFullYear(), now.getMonth() - 1, 1);
        end = new Date(now.getFullYear(), now.getMonth(), 0);
        break;
      case "thisYear":
        start = new Date(now.getFullYear(), 0, 1);
        end = new Date(now.getFullYear(), 11, 31);
        break;
      case "lastYear":
        start = new Date(now.getFullYear() - 1, 0, 1);
        end = new Date(now.getFullYear() - 1, 11, 31);
        break;
      case "custom":
        if (this.state.selectedDateRange) {
          start = this.state.selectedDateRange.start;
          end = this.state.selectedDateRange.end;
        }
        break;
    }

    this.state.selectedPeriod = period;
    if (start && end) {
      this.state.selectedDateRange = {
        start: this.formatDate(start),
        end: this.formatDate(end),
      };
    }
  }
}

OwlGuruDashboard.template = "owl.OwlGuruDashboard";
OwlGuruDashboard.components = {
  GuruKpiCard,
  GuruChartRenderer,
  GuruList,
  EkskulList,
};

registry.category("actions").add("owl.guru_dashboard", OwlGuruDashboard);