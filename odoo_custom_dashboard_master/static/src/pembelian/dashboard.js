import { registry } from "@web/core/registry";
import { PembelianKpiCard } from "./kpi_card/kpi_card";
import { PembelianChartRenderer } from "./chart_renderer/chart_renderer";
import { PembelianList } from "./card_list/card_list";

const { Component } = owl;

export class OwlPembelianDashboard extends Component {
  setup() {}
}

OwlPembelianDashboard.template = "owl.OwlPembelianDashboard";

OwlPembelianDashboard.components = {
  PembelianKpiCard,
  PembelianChartRenderer,
  PembelianList,
};

registry
  .category("actions")
  .add("owl.pembelian_dashboard", OwlPembelianDashboard);
