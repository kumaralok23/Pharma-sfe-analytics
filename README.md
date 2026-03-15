# 💊 Pharma Sales Force Effectiveness (SFE) Analytics

> **A full-stack analytics solution** that helps a pharmaceutical company optimize how Medical Representatives (MRs) allocate field visits across doctors and territories to maximize prescription revenue.

---

## 🎯 Business Problem

A mid-sized pharma company with 24 sales reps across 8 territories and 3 products (CardioMax, DiabeCure, NeuroCalm) was experiencing:

- **Suboptimal call planning**: Reps spending 30–42% of visits on low-prescribing doctors
- **Territory blind spots**: Some high-potential territories underperforming vs market opportunity
- **No unified visibility**: Leadership lacked a single view of rep performance vs prescription outcomes
- **Reactive coaching**: Sales managers couldn't identify coaching needs until quarterly reviews

---

## 💡 Solution Approach

| Layer | Tool | What it Does |
|-------|------|-------------|
| Data Generation | Python | Synthetic but realistic dataset: 300 doctors, 24 reps, 6,467 visits, 1,727 Rx records |
| Data Warehouse | SQL (MySQL/PostgreSQL) | Normalized schema + 9 analytical KPI queries |
| ML Segmentation | Python + Scikit-learn | K-Means clustering to segment doctors into 4 actionable groups |
| EDA & Visuals | Matplotlib + Seaborn | Static executive dashboard (6 charts) |
| Interactive Dashboard | Streamlit + Plotly | 4-tab live dashboard with filters, alerts, and recommendations |

---

## 📁 Project Structure

```
pharma-sfe-analytics/
├── README.md
├── requirements.txt
├── data/
│   ├── generate_data.py          # Synthetic data generator
│   ├── territories.csv
│   ├── reps.csv
│   ├── doctors.csv
│   ├── visits.csv
│   ├── prescriptions.csv
│   ├── doctor_segments.csv       # ML output
│   └── rep_performance.csv       # Scored rep data
├── sql/
│   └── schema.sql                # Schema + 9 analytical KPI queries
├── analysis/
│   ├── sfe_analysis.py           # EDA + ML clustering
│   └── outputs/
│       └── sfe_dashboard.png     # Static executive dashboard
└── dashboard/
    └── app.py                    # Streamlit interactive app
```

---

## 📊 Key Findings (FY 2024 Simulation)

### Revenue Performance
- **Total Revenue**: ₹42.0M across 3 products
- **Top Product**: NeuroCalm (highest revenue due to price premium)
- **Best Quarter**: Q4 at ₹11.4M — indicates seasonal acceleration

### Rep Efficiency
- Top rep (Meera Iyer) scored **2.21 efficiency** — 54% calls on High-potential doctors, ₹3.47M revenue
- Bottom reps scored **~1.13** — 41%+ calls on Low-potential doctors, ₹1.19M revenue (3x gap)
- **5 reps flagged** for over-calling Low-potential doctors (>35% of calls wasted)

### ML Doctor Segmentation (K-Means, K=3, Silhouette=0.353)
| Segment | Count | Avg Revenue | Avg Visits | Action |
|---------|-------|-------------|------------|--------|
| 🟢 High Value – Well Covered | 117 | ₹2,54,239 | 23.9 | Maintain |
| 🟡 Low Value – Low Coverage | 183 | ₹67,120 | 20.0 | Monitor only |

### Territory Insights
- Market capture ranges from ~8% to ~28% across territories
- Low-capture territories indicate either rep misallocation or doctor targeting mismatch

---

## 🚀 How to Run

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Generate synthetic data
```bash
python data/generate_data.py
```

### 3. Run Python analysis + save outputs
```bash
python analysis/sfe_analysis.py
```

### 4. Launch interactive dashboard
```bash
streamlit run dashboard/app.py
```

### 5. (Optional) Load SQL schema
```bash
# In MySQL or PostgreSQL:
mysql -u root -p your_db < sql/schema.sql
```

---

## 🧠 Methodology

### Rep Efficiency Score
```
Efficiency Score = (High_calls × 3 + Medium_calls × 1.5 + Low_calls × 0.5) / Total_calls
```
Reps scoring above median are well-aligned; below median need coaching on targeting.

### Doctor Segmentation (K-Means)
Features used: `potential_score`, `total_visits`, `total_revenue`, `unique_products`, `months_active`

All features scaled with `StandardScaler`. Optimal K selected via Silhouette Score across K=2–7.

---

## 📈 Business Impact Potential

If bottom-5 reps realigned calls from Low → High potential doctors:
- Estimated **30% revenue uplift** per rep (~₹500K–₹800K additional per rep annually)
- Across 5 reps = **₹2.5M–₹4M incremental revenue** with zero additional headcount

---

## 🛠 Tech Stack

`Python 3.10+` · `Pandas` · `NumPy` · `Scikit-learn` · `Matplotlib` · `Seaborn` · `Streamlit` · `Plotly` · `SQL`

---

## 👤 Author

**Alok Kumar Behera**
Associate Manager – Analytics, Jindal Stainless Limited
[alok2002behera@gmail.com](mailto:alok2002behera@gmail.com) | [LinkedIn](https://linkedin.com/in/alokkumar)

> *This project was built to demonstrate end-to-end data analytics and technology consulting capability, with specific alignment to pharmaceutical Sales Force Effectiveness — a core practice area at ZS Associates.*
