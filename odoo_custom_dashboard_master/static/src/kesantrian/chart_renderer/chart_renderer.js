/** @odoo-module */
import { registry } from "@web/core/registry";
import { loadJS } from "@web/core/assets";
const {
  Component,
  onWillStart,
  useRef,
  onMounted,
  onWillUnmount,
  onWillUpdateProps,
} = owl;
import { useService } from "@web/core/utils/hooks";

export class ChartRenderer extends Component {
  static props = {
    type: { type: String }, // 'chart' atau 'donutChart'
    period: { type: String, optional: true },
    startDate: { type: String, optional: true },
    endDate: { type: String, optional: true },
  };

  setup() {
    this.chartRef = useRef("chart");
    this.donutChartRef = useRef("donutChart");
    this.orm = useService("orm");
    this.actionService = useService("action");

    this.state = {
      chartData: { series: [], labels: [] },
      donutChartData: { labels: [], series: [] },
      currentStartDate: this.props.startDate,
      currentEndDate: this.props.endDate,
      isFiltered: !!(this.props.startDate && this.props.endDate),
    };

    this.chartInstance = null;
    this.donutChartInstance = null;

    onWillUpdateProps(async (nextProps) => {
      if (
        nextProps.startDate !== this.props.startDate ||
        nextProps.endDate !== this.props.endDate
      ) {
        this.showLoading();
        try {
          this.state.currentStartDate = nextProps.startDate;
          this.state.currentEndDate = nextProps.endDate;
          this.state.isFiltered = !!(nextProps.startDate && nextProps.endDate);
          await this.fetchHalaqohAttendanceData(
            nextProps.startDate,
            nextProps.endDate
          );
        } finally {
          this.hideLoading();
        }
      }
    });

    onWillStart(async () => {
      this.showLoading();
      try {
        await loadJS("https://cdn.jsdelivr.net/npm/apexcharts");
        await this.fetchHalaqohAttendanceData(
          this.state.currentStartDate,
          this.state.currentEndDate
        );
      } finally {
        this.hideLoading();
      }
    });

    onMounted(() => {
      this.renderChartIfNeeded();
    });

    onWillUnmount(() => {
      this.cleanup();
    });
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
        </div>
      `;
      document.body.appendChild(this.loadingOverlay);
    }
    this.loadingOverlay.style.display = "flex";
  }

  hideLoading() {
    if (this.loadingOverlay) {
      this.loadingOverlay.style.display = "none";
    }
  }

  cleanup() {
    if (this.chartInstance) {
      this.chartInstance.destroy();
      this.chartInstance = null;
    }
    if (this.donutChartInstance) {
      this.donutChartInstance.destroy();
      this.donutChartInstance = null;
    }
  }

  async fetchHalaqohAttendanceData(startDate = null, endDate = null) {
    // Tentukan rentang default (7 hari terakhir)
    let start, end;
    if (!startDate && !endDate) {
      const today = new Date();
      const weekAgo = new Date();
      weekAgo.setDate(today.getDate() - 6);
      start = weekAgo.toISOString().split("T")[0];
      end = today.toISOString().split("T")[0];
    } else {
      start = new Date(startDate).toISOString().split("T")[0];
      end = new Date(endDate).toISOString().split("T")[0];
    }

    const domain = [
      ["tanggal", ">=", start],
      ["tanggal", "<=", end],
    ];

    try {
      const data = await this.orm.call(
        "cdn.absen_halaqoh_line",
        "search_read",
        [domain, ["name", "halaqoh_id", "tanggal", "kehadiran"]]
      );

      // Group by halaqoh
      const halaqohMap = {};
      const statusCount = {};

      data.forEach((record) => {
        const halaqohName = record.halaqoh_id ? record.halaqoh_id[1] : "Tanpa Halaqoh";
        const status = record.kehadiran || "Tidak Ada Status";

        // Hitung per halaqoh
        if (!halaqohMap[halaqohName]) {
          halaqohMap[halaqohName] = { count: 0, ids: [] };
        }
        halaqohMap[halaqohName].count += 1;
        halaqohMap[halaqohName].ids.push(record.id);

        // Hitung status kehadiran
        statusCount[status] = (statusCount[status] || 0) + 1;
      });

      // Siapkan data untuk chart batang (per halaqoh)
      const halaqohNames = Object.keys(halaqohMap).sort();
      this.state.chartData = {
        labels: ["Total"],
        series: halaqohNames.map((name) => ({
          name: name,
          data: [halaqohMap[name].count],
          associated_ids: halaqohMap[name].ids,
        })),
      };

      // Siapkan data untuk donat (status kehadiran)
      this.state.donutChartData = {
        labels: Object.keys(statusCount),
        series: Object.values(statusCount),
      };

      this.renderChartIfNeeded();
    } catch (error) {
      console.error("Error fetching halaqoh attendance data:", error);
      this.state.chartData = { series: [], labels: [] };
      this.state.donutChartData = { labels: [], series: [] };
    }
  }

  renderChartIfNeeded() {
    if (this.props.type === "chart") {
      this.renderChart();
    } else if (this.props.type === "donutChart") {
      this.renderDonutChart();
    }
  }

  getChartConfig() {
    return {
      chart: {
        type: "bar",
        height: "100%",
        stacked: false,
        toolbar: { show: false },
        animations: { enabled: true, easing: "easeinout", speed: 800 },
        events: {
          dataPointSelection: (event, chartContext, config) =>
            this.onChartClick(event, chartContext, config),
        },
      },
      colors: [
        "#16a34a", "#0891b2", "#22c55e", "#06b6d4", "#15803d",
        "#0e7490", "#86efac", "#67e8f9", "#166534", "#155e75"
      ],
      legend: { position: "bottom" },
      xaxis: {
        type: "category",
        categories: this.state.chartData.labels,
        labels: {
          style: { fontSize: "12px", fontFamily: "Inter, sans-serif" },
          rotate: -45,
          formatter: (val) => (val.length > 15 ? val.substring(0, 15) + "..." : val),
        },
      },
      plotOptions: {
        bar: {
          columnWidth: "55%",
          borderRadius: 4,
          groupPadding: 0.3,
        },
      },
      stroke: { width: 2, colors: ["transparent"] },
      dataLabels: { enabled: false },
      yaxis: {
        labels: { formatter: (val) => Math.round(val) },
      },
      tooltip: {
        shared: true,
        intersect: false,
        y: { formatter: (val) => Math.round(val) },
      },
      noData: {
        text: "Tidak ada data",
        align: "center",
        verticalAlign: "middle",
        style: { color: "#1f2937", fontSize: "16px", fontFamily: "Inter" },
      },
    };
  }

  getDonutChartConfig() {
    return {
      chart: {
        type: "pie",
        height: "100%",
        toolbar: { show: false },
        animations: { enabled: true, easing: "easeinout", speed: 800 },
        events: {
          dataPointSelection: (event, chartContext, config) =>
            this.onDonutClick(event, chartContext, config),
        },
      },
      legend: { position: "top", horizontalAlign: "center" },
      dataLabels: { enabled: false },
      colors: [
        "#16a34a", "#0891b2", "#22c55e", "#06b6d4", "#15803d",
        "#0e7490", "#86efac", "#67e8f9", "#166534", "#155e75"
      ],
      labels: this.state.donutChartData.labels,
      series: this.state.donutChartData.series,
      tooltip: {
        y: { formatter: (val) => val + " orang" },
      },
      noData: {
        text: "Tidak ada data",
        align: "center",
        verticalAlign: "middle",
        style: { color: "#1f2937", fontSize: "16px", fontFamily: "Inter" },
      },
    };
  }

  renderChart() {
    if (!this.chartRef.el) return;
    this.cleanupChartOnly();
    const config = { ...this.getChartConfig(), series: this.state.chartData.series };
    try {
      this.chartInstance = new ApexCharts(this.chartRef.el, config);
      this.chartInstance.render();
    } catch (error) {
      console.error("Error rendering bar chart:", error);
    }
  }

  renderDonutChart() {
    if (!this.donutChartRef.el) return;
    this.cleanupDonutOnly();
    const config = this.getDonutChartConfig();
    try {
      this.donutChartInstance = new ApexCharts(this.donutChartRef.el, config);
      this.donutChartInstance.render();
    } catch (error) {
      console.error("Error rendering donut chart:", error);
    }
  }

  cleanupChartOnly() {
    if (this.chartInstance) {
      this.chartInstance.destroy();
      this.chartInstance = null;
    }
  }

  cleanupDonutOnly() {
    if (this.donutChartInstance) {
      this.donutChartInstance.destroy();
      this.donutChartInstance = null;
    }
  }

  onChartClick(event, chartContext, config) {
    const { dataPointIndex, seriesIndex } = config;
    if (dataPointIndex === -1) return;

    const associatedIds = this.state.chartData.series[seriesIndex].associated_ids;
    if (!associatedIds || associatedIds.length === 0) return;

    this.actionService.doAction({
      type: "ir.actions.act_window",
      name: "Detail Absensi Halaqoh",
      res_model: "cdn.absen_halaqoh_line",
      view_mode: "list,form",
      domain: [["id", "in", associatedIds]],
      views: [[false, "list"], [false, "form"]],
      target: "current",
    });
  }

  onDonutClick(event, chartContext, config) {
    const dataPointIndex = config.dataPointIndex;
    if (dataPointIndex === -1) return;

    const status = this.state.donutChartData.labels[dataPointIndex];
    const domain = [["kehadiran", "=", status]];

    if (this.state.currentStartDate && this.state.currentEndDate) {
      domain.push(
        ["tanggal", ">=", this.state.currentStartDate],
        ["tanggal", "<=", this.state.currentEndDate]
      );
    }

    this.actionService.doAction({
      type: "ir.actions.act_window",
      name: `Absensi Halaqoh - ${status}`,
      res_model: "cdn.absen_halaqoh_line",
      view_mode: "list,form",
      domain: domain,
      views: [[false, "list"], [false, "form"]],
      target: "current",
    });
  }
}

ChartRenderer.template = "owl.ChartRenderer";