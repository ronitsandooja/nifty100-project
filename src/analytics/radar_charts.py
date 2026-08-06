import sqlite3
from pathlib import Path

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.screener.engine import build_universe, compute_composite_scores

AXES = ["roe", "roce", "npm", "de", "fcf", "pat_cagr_5yr", "revenue_cagr_5yr", "composite_score"]
AXIS_LABELS = ["ROE", "ROCE", "NPM", "D/E", "FCF", "PAT CAGR 5yr", "Rev CAGR 5yr", "Composite"]


def load_data(db_path="db/nifty100.db"):
    conn = sqlite3.connect(db_path)
    percentiles = pd.read_sql("select * from peer_percentiles", conn)
    peer_groups = pd.read_sql("select * from peer_groups", conn)
    companies = pd.read_sql("select * from companies", conn)
    fr_history = pd.read_sql("select * from financial_ratios", conn)
    conn.close()

    universe = build_universe(db_path)
    universe = compute_composite_scores(universe, fr_history)

    return percentiles, peer_groups, companies, universe


def company_radar_values(company_id, peer_group_name, percentiles, composite_score):
    values = []
    for metric in AXES[:-1]:
        row = percentiles[
            (percentiles["company_id"] == company_id) &
            (percentiles["peer_group_name"] == peer_group_name) &
            (percentiles["metric"] == metric)
        ]
        values.append(row["percentile_rank"].iloc[0] * 100 if not row.empty else 0)

    values.append(composite_score if composite_score is not None and not pd.isna(composite_score) else 0)
    return values


def peer_group_average_values(peer_group_name, member_ids, percentiles, universe):
    values = []
    for metric in AXES[:-1]:
        rows = percentiles[(percentiles["peer_group_name"] == peer_group_name) & (percentiles["metric"] == metric)]
        values.append(rows["percentile_rank"].mean() * 100 if not rows.empty else 0)

    member_scores = universe[universe["company_id"].isin(member_ids)]["composite_score"]
    values.append(member_scores.mean() if not member_scores.empty else 0)
    return values


def draw_radar(company_id, company_values, peer_avg_values, output_path):
    angle_step = 2 * np.pi / len(AXES)
    angles = [angle_step * i for i in range(len(AXES))]

    company_plot = company_values + company_values[:1]
    peer_plot = peer_avg_values + peer_avg_values[:1]
    angles_plot = angles + angles[:1]

    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw={"polar": True})
    ax.plot(angles_plot, company_plot, color="#2c7fb8", linewidth=2)
    ax.fill(angles_plot, company_plot, color="#2c7fb8", alpha=0.25)
    ax.plot(angles_plot, peer_plot, color="gray", linewidth=1.5, linestyle="--")

    ax.set_xticks(angles)
    ax.set_xticklabels(AXIS_LABELS, fontsize=9)
    ax.set_ylim(0, 100)
    ax.set_title(company_id, fontsize=13, pad=20)

    fig.savefig(output_path, dpi=100, bbox_inches="tight")
    plt.close(fig)


def draw_standalone(company_id, composite_score, universe_avg, output_path):
    score = composite_score if composite_score is not None and not pd.isna(composite_score) else 0

    fig, ax = plt.subplots(figsize=(5, 2))
    ax.barh(["Nifty 100 avg", company_id], [universe_avg, score], color=["gray", "#2c7fb8"])
    ax.set_xlim(0, 100)
    ax.set_xlabel("Composite Score")
    ax.set_title(f"{company_id} - No peer group assigned")

    fig.savefig(output_path, dpi=100, bbox_inches="tight")
    plt.close(fig)


def generate_all_radar_charts(output_dir="reports/radar_charts"):
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    percentiles, peer_groups, companies, universe = load_data()
    universe_avg = universe["composite_score"].mean()

    count = 0
    for _, company in companies.iterrows():
        company_id = company["id"]
        membership = peer_groups[peer_groups["company_id"] == company_id]

        row = universe[universe["company_id"] == company_id]
        composite_score = row["composite_score"].iloc[0] if not row.empty else None

        output_path = f"{output_dir}/{company_id}_radar.png"

        if membership.empty:
            draw_standalone(company_id, composite_score, universe_avg, output_path)
        else:
            peer_group_name = membership["peer_group_name"].iloc[0]
            member_ids = peer_groups[peer_groups["peer_group_name"] == peer_group_name]["company_id"].tolist()

            company_values = company_radar_values(company_id, peer_group_name, percentiles, composite_score)
            peer_avg_values = peer_group_average_values(peer_group_name, member_ids, percentiles, universe)

            draw_radar(company_id, company_values, peer_avg_values, output_path)

        count += 1

    return count


if __name__ == "__main__":
    n = generate_all_radar_charts()
    print(f"generated {n} radar charts in reports/radar_charts/")
