import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";

export class ScoreButtonsWidget extends Component {
  static template = "xink_purchase.ScoreButtonsWidget";

  get scoreRange() {
    let scoreScale = this.props.record.data.score_scale;
    if (!scoreScale && this.props.record.data.evaluation_id) {
      const evaluationData = this.props.record.data.evaluation_id;
      if (evaluationData && evaluationData.score_scale) {
        scoreScale = evaluationData.score_scale;
      }
    }
    scoreScale = scoreScale || "5";
    if (scoreScale === "boolean") {
      return { min: 0, max: 10, isBoolean: true };
    }
    const maxScore = parseInt(scoreScale);
    return { min: 0, max: maxScore, isBoolean: false };
  }

  get currentScore() {
    const value = this.props.record.data[this.props.name];
    // Nếu là boolean thì value có thể là string '10' hoặc '0'
    if (this.scoreRange.isBoolean) {
      return value === "10" || value === 10 ? 10 : 0;
    }
    const score = value ? parseInt(value) : 0;
    return score;
  }

  get scoreButtons() {
    const { min, max, isBoolean } = this.scoreRange;
    const currentScore = this.currentScore;
    const buttons = [];
    if (isBoolean) {
      buttons.push({
        value: 0,
        label: "Không đạt",
        isActive: currentScore === 0,
        cssClass: `btn btn-sm score-btn me-1 mb-1 ${
          currentScore === 0 ? "btn-danger" : "btn-outline-danger"
        }`,
      });
      buttons.push({
        value: 10,
        label: "Đạt",
        isActive: currentScore === 10,
        cssClass: `btn btn-sm score-btn me-1 mb-1 ${
          currentScore === 10 ? "btn-success" : "btn-outline-success"
        }`,
      });
    } else {
      for (let i = min; i <= max; i++) {
        buttons.push({
          value: i,
          label: i,
          isActive: currentScore === i,
          cssClass: `btn btn-sm score-btn me-1 mb-1 ${
            currentScore === i ? "btn-primary" : "btn-outline-primary"
          }`,
        });
      }
    }
    return buttons;
  }

  onScoreClick(value) {
    if (!this.props.readonly) {
      // Nếu là boolean thì lưu giá trị là '10' hoặc '0' (string)
      if (this.scoreRange.isBoolean) {
        this.props.record.update({
          [this.props.name]: value === 10 ? "10" : "0",
        });
      } else {
        this.props.record.update({
          [this.props.name]: value,
        });
      }
    }
  }
}

registry.category("fields").add("score_buttons", {
  component: ScoreButtonsWidget,
});
