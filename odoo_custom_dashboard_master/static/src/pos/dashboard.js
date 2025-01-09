/** @odoo-module */
import { registry } from "@web/core/registry";
import { PosKpiCard } from "./kpi_card/pos_kpi_card";
import { PosChartRenderer } from "./chart_renderer/pos_chart_renderer";
import { PosCardList, PosCardList1 } from "./card_list/pos_card_list";
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart } from "@odoo/owl";

export class OwlPosDashboard extends Component {
  setup() {
    this.orm = useService("orm");
    this.state = {
      stores: [],
      selectedStore: null,
    };

    onWillStart(async () => {
      await this.fetchStores();
    });
  }

  async fetchStores() {
    try {
      const stores = await this.orm.call(
        "pos.config",
        "search_read",
        [[], ["id", "name"]],
        { order: "name asc" }
      );
      this.state.stores = stores;
    } catch (error) {
      console.error("Error fetching stores:", error);
    }
  }

  handleStoreChange(event) {
    const selectedStoreId = parseInt(event.target.value);
    this.state.selectedStore = selectedStoreId || null;
    // You might need to trigger a refresh of your charts here
  }
}

OwlPosDashboard.template = "owl.OwlPosDashboard";
OwlPosDashboard.components = {
  PosKpiCard,
  PosChartRenderer,
  PosCardList,
  PosCardList1,
};

registry.category("actions").add("owl.pos_dashboard", OwlPosDashboard);
