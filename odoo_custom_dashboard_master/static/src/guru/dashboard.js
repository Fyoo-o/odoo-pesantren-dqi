import { registry } from "@web/core/registry";
import { GuruKpiCard } from "./kpi_card/kpi_card";
import { GuruChartRenderer } from "./chart_renderer/chart_renderer";
import { GuruList } from "./card_list/card_list";

// GAREK KPI CARD

const { Component } = owl;

export class OwlGuruDashboard extends Component {
  setup() {}
}

OwlGuruDashboard.template = "owl.OwlGuruDashboard";

OwlGuruDashboard.components = {
  GuruKpiCard,
  GuruChartRenderer,
  GuruList,
};

registry.category("actions").add("owl.guru_dashboard", OwlGuruDashboard);
