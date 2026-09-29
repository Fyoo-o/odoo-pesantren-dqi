/** @odoo-module **/
import { Component, onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class OrangtuaPengumumanCard extends Component {
  static template = "owl.OrangtuaPengumumanCard";

  setup() {
    this.orm = useService("orm");
    this.actionService = useService("action");
    this.state = {
      pengumumanList: [],
      isLoading: true,
      hasData: false,
    };

    onWillStart(async () => {
      await this.fetchPengumuman();
    });
  }

  async fetchPengumuman() {
    try {
      this.state.isLoading = true;
      const records = await this.orm.searchRead(
        "cdn.pengumuman",
        [],
        ["id", "name", "deskripsi", "create_date"],
        { order: "id desc", limit: 6 }
      );

      if (records && records.length > 0) {
        this.state.pengumumanList = records.map((rec) => {
          let dateStr = "";
          if (rec.create_date) {
            const d = new Date(rec.create_date);
            const months = [
              "Jan", "Feb", "Mar", "Apr", "Mei", "Jun",
              "Jul", "Ags", "Sep", "Okt", "Nov", "Des"
            ];
            dateStr = `${d.getDate()} ${months[d.getMonth()]} ${d.getFullYear()}`;
          }
          let textPreview = "";
          if (rec.deskripsi) {
            const tempDiv = document.createElement("div");
            tempDiv.innerHTML = rec.deskripsi;
            textPreview = tempDiv.textContent || tempDiv.innerText || "";
            if (textPreview.length > 140) {
              textPreview = textPreview.substring(0, 140) + "...";
            }
          }
          return {
            id: rec.id,
            name: rec.name,
            date: dateStr,
            preview: textPreview,
          };
        });
        this.state.hasData = true;
      } else {
        this.state.pengumumanList = [];
        this.state.hasData = false;
      }
    } catch (err) {
      console.error("Error fetching pengumuman:", err);
      this.state.hasData = false;
    } finally {
      this.state.isLoading = false;
    }
  }

  onPengumumanClick(id) {
    this.actionService.doAction({
      type: "ir.actions.act_window",
      res_model: "cdn.pengumuman",
      res_id: id,
      views: [[false, "form"]],
      target: "current",
    });
  }

  openAllPengumuman() {
    this.actionService.doAction({
      type: "ir.actions.act_window",
      name: "Pengumuman Pesantren",
      res_model: "cdn.pengumuman",
      views: [[false, "list"], [false, "form"]],
      target: "current",
    });
  }
}
