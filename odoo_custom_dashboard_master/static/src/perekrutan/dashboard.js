import { registry } from "@web/core/registry";
import { PerekrutanChartRenderer } from "./chart_renderer/chart_renderer";
import { PerekrutanList } from "./card_list/card_list";
import { PerekrutanKpiCard } from "./kpi_card/kpi_card";

const { Component } = owl;

export class OwlPerekrutanDashboard extends Component {
  setup() {}
}

OwlPerekrutanDashboard.template = "owl.OwlPerekrutanDashboard";

OwlPerekrutanDashboard.components = {
  PerekrutanKpiCard,
  PerekrutanChartRenderer,
  PerekrutanList,
};

registry
  .category("actions")
  .add("owl.perekrutan_dashboard", OwlPerekrutanDashboard);
