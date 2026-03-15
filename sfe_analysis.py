"""
Pharma SFE Analytics — Python Analysis & ML Doctor Segmentation
Includes: EDA, Rep Efficiency Scoring, K-Means Doctor Clustering, Insights
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import warnings, os

warnings.filterwarnings("ignore")

BASE   = os.path.dirname(os.path.abspath(__file__))
DATA   = os.path.join(BASE, "../data")
OUT    = os.path.join(BASE, "outputs")
os.makedirs(OUT, exist_ok=True)

PALETTE = {"High": "#2ECC71", "Medium": "#F39C12", "Low": "#E74C3C"}
PROD_COLORS = {"CardioMax": "#3498DB", "DiabeCure": "#9B59B6", "NeuroCalm": "#E67E22"}
BLUE   = "#1F4E79"

# ── LOAD DATA ────────────────────────────────────────────────────────────────
territories   = pd.read_csv(f"{DATA}/territories.csv")
reps          = pd.read_csv(f"{DATA}/reps.csv")
doctors       = pd.read_csv(f"{DATA}/doctors.csv")
visits        = pd.read_csv(f"{DATA}/visits.csv")
prescriptions = pd.read_csv(f"{DATA}/prescriptions.csv")

print("=" * 60)
print("  PHARMA SFE ANALYTICS — PYTHON ANALYSIS REPORT")
print("=" * 60)

# ═══════════════════════════════════════════════════════════════
# ANALYSIS 1: OVERALL KPI SUMMARY
# ═══════════════════════════════════════════════════════════════
total_revenue = prescriptions["revenue"].sum()
total_visits  = len(visits)
unique_docs_visited = visits["doctor_id"].nunique()
avg_freq = visits.groupby("doctor_id").size().mean()
top_product = prescriptions.groupby("product")["revenue"].sum().idxmax()

print(f"\n📊 PORTFOLIO SUMMARY (FY 2024)")
print(f"   Total Revenue       : ₹{total_revenue:,.0f}")
print(f"   Total Field Visits  : {total_visits:,}")
print(f"   Doctors Reached     : {unique_docs_visited} / {len(doctors)}")
print(f"   Avg Visit Frequency : {avg_freq:.1f} visits/doctor")
print(f"   Top Revenue Product : {top_product}")

# ═══════════════════════════════════════════════════════════════
# ANALYSIS 2: REP EFFICIENCY SCORING
# ═══════════════════════════════════════════════════════════════
visit_doc = visits.merge(doctors[["doctor_id","prescribing_potential","potential_score"]], on="doctor_id")

rep_calls = visit_doc.groupby(["rep_id","prescribing_potential"]).size().unstack(fill_value=0).reset_index()
rep_calls.columns.name = None
for col in ["High","Medium","Low"]:
    if col not in rep_calls.columns:
        rep_calls[col] = 0

rep_calls["total_calls"] = rep_calls[["High","Medium","Low"]].sum(axis=1)
rep_calls["efficiency_score"] = (
    (rep_calls["High"] * 3 + rep_calls["Medium"] * 1.5 + rep_calls["Low"] * 0.5)
    / rep_calls["total_calls"]
).round(2)
rep_calls["high_pct"] = (rep_calls["High"] / rep_calls["total_calls"] * 100).round(1)
rep_calls["low_pct"]  = (rep_calls["Low"]  / rep_calls["total_calls"] * 100).round(1)

rep_revenue = prescriptions.merge(
    visits[["visit_id","rep_id","doctor_id","month","product"]].drop_duplicates(),
    on=["doctor_id","product","month"], how="left"
).groupby("rep_id")["revenue"].sum().reset_index().rename(columns={"revenue":"total_revenue"})

rep_perf = rep_calls.merge(reps[["rep_id","rep_name","target_calls","experience_yrs"]], on="rep_id")
rep_perf = rep_perf.merge(rep_revenue, on="rep_id", how="left").fillna(0)
rep_perf["call_achievement_pct"] = (rep_perf["total_calls"] / rep_perf["target_calls"] * 100).round(1)
rep_perf["revenue_per_call"] = (rep_perf["total_revenue"] / rep_perf["total_calls"]).round(0)

print(f"\n🏆 TOP 5 REPS BY EFFICIENCY SCORE")
top5 = rep_perf.nlargest(5, "efficiency_score")[
    ["rep_name","efficiency_score","high_pct","low_pct","total_revenue"]
]
for _, row in top5.iterrows():
    print(f"   {row['rep_name']:<22} Score:{row['efficiency_score']:.2f}  "
          f"High%:{row['high_pct']:.0f}%  Low%:{row['low_pct']:.0f}%  "
          f"Rev:₹{row['total_revenue']:,.0f}")

print(f"\n⚠️  BOTTOM 5 REPS (Over-calling Low-potential Doctors)")
bot5 = rep_perf.nlargest(5, "low_pct")[
    ["rep_name","low_pct","high_pct","efficiency_score","total_revenue"]
]
for _, row in bot5.iterrows():
    print(f"   {row['rep_name']:<22} Low%:{row['low_pct']:.0f}%  "
          f"High%:{row['high_pct']:.0f}%  Score:{row['efficiency_score']:.2f}  "
          f"Rev:₹{row['total_revenue']:,.0f}")

# ═══════════════════════════════════════════════════════════════
# ANALYSIS 3: ML — K-MEANS DOCTOR SEGMENTATION
# ═══════════════════════════════════════════════════════════════
doc_visits    = visits.groupby("doctor_id").agg(
    total_visits=("visit_id","count"),
    unique_products=("product","nunique"),
    avg_duration=("duration_min","mean"),
    samples_received=("samples_left","sum"),
).reset_index()

doc_revenue   = prescriptions.groupby("doctor_id").agg(
    total_revenue=("revenue","sum"),
    total_units=("units_prescribed","sum"),
    months_active=("month","nunique"),
).reset_index()

doc_features  = doctors[["doctor_id","potential_score","years_in_practice"]].merge(
    doc_visits,  on="doctor_id", how="left"
).merge(doc_revenue, on="doctor_id", how="left").fillna(0)

FEATURES = ["potential_score","total_visits","total_revenue","unique_products","months_active"]
X = doc_features[FEATURES].copy()
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Elbow method to find optimal K
inertias, sil_scores = [], []
K_range = range(2, 8)
for k in K_range:
    km = KMeans(n_clusters=k, random_state=42, n_init=10)
    km.fit(X_scaled)
    inertias.append(km.inertia_)
    sil_scores.append(silhouette_score(X_scaled, km.labels_))

best_k = K_range[np.argmax(sil_scores)]
km_final = KMeans(n_clusters=best_k, random_state=42, n_init=10)
doc_features["cluster"] = km_final.fit_predict(X_scaled)

# Label clusters based on centroid characteristics
cluster_summary = doc_features.groupby("cluster")[FEATURES].mean()
cluster_summary["label"] = ""
for idx, row in cluster_summary.iterrows():
    if row["total_revenue"] > cluster_summary["total_revenue"].median() and row["total_visits"] > cluster_summary["total_visits"].median():
        cluster_summary.at[idx, "label"] = "🟢 High Value - Well Covered"
    elif row["total_revenue"] > cluster_summary["total_revenue"].median() and row["total_visits"] <= cluster_summary["total_visits"].median():
        cluster_summary.at[idx, "label"] = "🔵 High Value - Under-visited"
    elif row["total_revenue"] <= cluster_summary["total_revenue"].median() and row["total_visits"] > cluster_summary["total_visits"].median():
        cluster_summary.at[idx, "label"] = "🔴 Low Value - Over-visited"
    else:
        cluster_summary.at[idx, "label"] = "🟡 Low Value - Low Coverage"

doc_features["segment"] = doc_features["cluster"].map(cluster_summary["label"])

print(f"\n🤖 ML DOCTOR SEGMENTATION (K={best_k} clusters, Silhouette={max(sil_scores):.3f})")
for label, grp in doc_features.groupby("segment"):
    print(f"   {label:<38} n={len(grp):>3}  "
          f"Avg Rev:₹{grp['total_revenue'].mean():>8,.0f}  "
          f"Avg Visits:{grp['total_visits'].mean():>5.1f}")

# ═══════════════════════════════════════════════════════════════
# ANALYSIS 4: PRODUCT TREND ANALYSIS
# ═══════════════════════════════════════════════════════════════
monthly = prescriptions.groupby(["month","product"])["revenue"].sum().reset_index()
pivot   = monthly.pivot(index="month", columns="product", values="revenue").fillna(0)

print(f"\n📈 QUARTERLY REVENUE BREAKDOWN (₹)")
for q in range(1,5):
    months = list(range((q-1)*3+1, q*3+1))
    q_rev = prescriptions[prescriptions["month"].isin(months)]["revenue"].sum()
    print(f"   Q{q}: ₹{q_rev:,.0f}")

# ═══════════════════════════════════════════════════════════════
# VISUALIZATIONS
# ═══════════════════════════════════════════════════════════════
plt.rcParams.update({"font.family":"DejaVu Sans", "axes.spines.top":False, "axes.spines.right":False})

fig, axes = plt.subplots(2, 3, figsize=(18, 11))
fig.suptitle("Pharma SFE Analytics — Executive Dashboard", fontsize=16, fontweight="bold", color=BLUE, y=0.98)

# Plot 1: Rep Efficiency Scores
ax = axes[0, 0]
rep_sorted = rep_perf.sort_values("efficiency_score", ascending=True).tail(12)
colors = ["#E74C3C" if s < rep_perf["efficiency_score"].median() else "#2ECC71" for s in rep_sorted["efficiency_score"]]
ax.barh(rep_sorted["rep_name"], rep_sorted["efficiency_score"], color=colors, edgecolor="white", height=0.7)
ax.axvline(rep_perf["efficiency_score"].median(), color=BLUE, linestyle="--", linewidth=1.5, label="Median")
ax.set_title("Rep Call Efficiency Score", fontweight="bold", color=BLUE)
ax.set_xlabel("Score (weighted by doctor potential)")
ax.legend(fontsize=8)

# Plot 2: Call Distribution by Doctor Potential
ax = axes[0, 1]
pot_dist = visit_doc.groupby(["rep_id","prescribing_potential"]).size().unstack(fill_value=0)
pot_dist_pct = pot_dist.div(pot_dist.sum(axis=1), axis=0) * 100
pot_dist_pct = pot_dist_pct.reindex(columns=["High","Medium","Low"])
pot_dist_pct.plot(kind="bar", ax=ax, color=["#2ECC71","#F39C12","#E74C3C"],
                   stacked=True, width=0.7, edgecolor="white", linewidth=0.5)
ax.set_title("Call Distribution by Doctor Potential (%)", fontweight="bold", color=BLUE)
ax.set_xlabel("Rep ID")
ax.set_ylabel("% of Total Calls")
ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha="right", fontsize=7)
ax.legend(title="Potential", bbox_to_anchor=(1,1), fontsize=8)
ax.axhline(60, color="gray", linestyle=":", linewidth=1)

# Plot 3: Monthly Revenue Trend by Product
ax = axes[0, 2]
for prod, color in PROD_COLORS.items():
    if prod in pivot.columns:
        ax.plot(pivot.index, pivot[prod]/1e6, marker="o", linewidth=2,
                markersize=5, color=color, label=prod)
ax.set_title("Monthly Revenue Trend by Product", fontweight="bold", color=BLUE)
ax.set_xlabel("Month")
ax.set_ylabel("Revenue (₹ Millions)")
ax.set_xticks(range(1,13))
ax.set_xticklabels(["J","F","M","A","M","J","J","A","S","O","N","D"])
ax.legend(fontsize=9)
ax.fill_between(pivot.index, pivot.sum(axis=1)/1e6, alpha=0.05, color=BLUE)

# Plot 4: ML Cluster Scatter — Visits vs Revenue
ax = axes[1, 0]
seg_colors = {
    "🟢 High Value - Well Covered":    "#2ECC71",
    "🔵 High Value - Under-visited":   "#3498DB",
    "🔴 Low Value - Over-visited":     "#E74C3C",
    "🟡 Low Value - Low Coverage":     "#F1C40F",
}
for seg, color in seg_colors.items():
    mask = doc_features["segment"] == seg
    ax.scatter(doc_features.loc[mask, "total_visits"],
               doc_features.loc[mask, "total_revenue"]/1000,
               c=color, alpha=0.6, s=40, label=seg.split(" ",1)[1], edgecolors="white", linewidths=0.3)
ax.set_title("Doctor Segmentation (ML Clusters)", fontweight="bold", color=BLUE)
ax.set_xlabel("Total Visits Received")
ax.set_ylabel("Revenue Generated (₹K)")
ax.legend(fontsize=7, loc="upper left")

# Plot 5: Territory Performance vs Market Potential
ax = axes[1, 1]
terr_rev = prescriptions.merge(territories[["territory_id","territory_name","market_potential"]], on="territory_id")
terr_agg = terr_rev.groupby(["territory_name","market_potential"])["revenue"].sum().reset_index()
terr_agg["capture_pct"] = terr_agg["revenue"] / terr_agg["market_potential"] * 100
bars = ax.bar(range(len(terr_agg)), terr_agg["capture_pct"],
              color=[BLUE if x >= terr_agg["capture_pct"].median() else "#AED6F1" for x in terr_agg["capture_pct"]],
              edgecolor="white")
ax.set_xticks(range(len(terr_agg)))
ax.set_xticklabels([n.replace(" Zone","") for n in terr_agg["territory_name"]],
                    rotation=30, ha="right", fontsize=8)
ax.axhline(terr_agg["capture_pct"].median(), color="#E74C3C", linestyle="--", linewidth=1.5, label="Median")
ax.set_title("Territory Market Capture (%)", fontweight="bold", color=BLUE)
ax.set_ylabel("% of Market Potential Captured")
ax.legend(fontsize=8)

# Plot 6: Product Revenue Share by Territory
ax = axes[1, 2]
prod_terr = prescriptions.merge(territories[["territory_id","territory_name"]], on="territory_id")
pt_pivot  = prod_terr.groupby(["territory_name","product"])["revenue"].sum().unstack(fill_value=0)
pt_pivot   = pt_pivot.div(pt_pivot.sum(axis=1), axis=0) * 100
pt_pivot.plot(kind="bar", ax=ax, color=list(PROD_COLORS.values()),
               stacked=True, width=0.7, edgecolor="white", linewidth=0.5)
ax.set_title("Product Revenue Mix by Territory (%)", fontweight="bold", color=BLUE)
ax.set_ylabel("Revenue Share (%)")
ax.set_xticklabels([n.replace(" Zone","") for n in pt_pivot.index],
                    rotation=30, ha="right", fontsize=8)
ax.legend(title="Product", bbox_to_anchor=(1,1), fontsize=8)

plt.tight_layout(rect=[0, 0, 1, 0.97])
plt.savefig(f"{OUT}/sfe_dashboard.png", dpi=150, bbox_inches="tight",
            facecolor="white", edgecolor="none")
plt.close()
print(f"\n✅ Dashboard saved → analysis/outputs/sfe_dashboard.png")

# Save enriched data for Streamlit
doc_features.to_csv(f"{DATA}/doctor_segments.csv", index=False)
rep_perf.to_csv(f"{DATA}/rep_performance.csv", index=False)
print("✅ Enriched datasets saved for Streamlit dashboard")
print("\n" + "=" * 60)
