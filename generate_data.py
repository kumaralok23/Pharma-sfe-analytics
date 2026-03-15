"""
Pharma SFE Analytics — Synthetic Data Generator
Generates realistic data for: Territories, Reps, Doctors, Visits, Prescriptions
"""

import pandas as pd
import numpy as np
import random
import os
from datetime import datetime, timedelta

np.random.seed(42)
random.seed(42)

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

# ── CONFIG ──────────────────────────────────────────────────────────────────
N_TERRITORIES  = 8
N_REPS         = 24       # 3 reps per territory
N_DOCTORS      = 300
N_MONTHS       = 12       # Jan–Dec 2024
PRODUCTS       = ["CardioMax", "DiabeCure", "NeuroCalm"]
SPECIALTIES    = ["Cardiologist","Diabetologist","Neurologist","General Physician","Internist"]
STATES         = ["Maharashtra","Karnataka","Tamil Nadu","Delhi","Gujarat",
                  "Rajasthan","West Bengal","Telangana"]

# ── 1. TERRITORIES ───────────────────────────────────────────────────────────
territory_ids = [f"T{str(i).zfill(2)}" for i in range(1, N_TERRITORIES+1)]
territories = pd.DataFrame({
    "territory_id":   territory_ids,
    "territory_name": [f"Zone {s}" for s in STATES],
    "state":          STATES,
    "region":         ["West","South","South","North","West","North","East","South"],
    "market_potential": np.random.randint(500_000, 2_000_000, N_TERRITORIES),
})

# ── 2. SALES REPS ─────────────────────────────────────────────────────────────
first = ["Rahul","Priya","Amit","Sneha","Vikram","Anjali","Rohan","Divya",
         "Karan","Meera","Suresh","Pooja","Nikhil","Aarti","Aditya","Ritu",
         "Sanjay","Kavya","Deepak","Nisha","Rajesh","Sonali","Manoj","Preeti"]
last  = ["Sharma","Verma","Singh","Patel","Gupta","Reddy","Kumar","Joshi",
         "Mishra","Iyer","Rao","Nair","Chopra","Mehta","Desai","Shah",
         "Tiwari","Pillai","Chauhan","Bose","Das","Saxena","Agarwal","Malhotra"]

rep_ids = [f"R{str(i).zfill(3)}" for i in range(1, N_REPS+1)]
reps = pd.DataFrame({
    "rep_id":        rep_ids,
    "rep_name":      [f"{first[i]} {last[i]}" for i in range(N_REPS)],
    "territory_id":  [territory_ids[i // 3] for i in range(N_REPS)],
    "experience_yrs": np.random.randint(1, 12, N_REPS),
    "target_calls":  np.random.randint(200, 320, N_REPS),
})

# ── 3. DOCTORS ────────────────────────────────────────────────────────────────
doc_ids = [f"D{str(i).zfill(4)}" for i in range(1, N_DOCTORS+1)]

# Prescribing potential: high/medium/low (drives visit priority)
potential = np.random.choice(["High","Medium","Low"], N_DOCTORS, p=[0.2, 0.5, 0.3])
potential_score = {"High": np.random.randint(80,100), "Medium": np.random.randint(40,79), "Low": np.random.randint(10,39)}

doc_territory = np.random.choice(territory_ids, N_DOCTORS)
doc_specialty  = np.random.choice(SPECIALTIES, N_DOCTORS)

doctors = pd.DataFrame({
    "doctor_id":          doc_ids,
    "doctor_name":        [f"Dr. {random.choice(first)} {random.choice(last)}" for _ in range(N_DOCTORS)],
    "specialty":          doc_specialty,
    "territory_id":       doc_territory,
    "prescribing_potential": potential,
    "potential_score":    [np.random.randint(*{
                              "High":(80,100),"Medium":(40,79),"Low":(10,39)
                           }[p]) for p in potential],
    "years_in_practice":  np.random.randint(2, 30, N_DOCTORS),
})

# ── 4. VISITS ─────────────────────────────────────────────────────────────────
visit_records = []
visit_id = 1
start_date = datetime(2024, 1, 1)

for _, rep in reps.iterrows():
    # Get doctors in same territory
    local_docs = doctors[doctors["territory_id"] == rep["territory_id"]]["doctor_id"].tolist()
    if not local_docs:
        continue

    # Reps visit ~22 doctors/month but distribute unequally by potential
    for month in range(N_MONTHS):
        n_visits = np.random.randint(18, 28)
        # Bias toward high-potential doctors (but not always — to show inefficiency)
        weights = []
        for d in local_docs:
            pot = doctors[doctors["doctor_id"]==d]["prescribing_potential"].values[0]
            # Some reps are "efficient", some are not — based on rep index
            rep_idx = rep_ids.index(rep["rep_id"])
            if rep_idx % 3 == 0:   # efficient rep
                w = {"High": 5, "Medium": 2, "Low": 1}[pot]
            elif rep_idx % 3 == 1: # average rep
                w = {"High": 3, "Medium": 2, "Low": 2}[pot]
            else:                   # inefficient rep (calls on low-value docs)
                w = {"High": 1, "Medium": 2, "Low": 4}[pot]
            weights.append(w)

        total_w = sum(weights)
        probs = [w/total_w for w in weights]
        visited = np.random.choice(local_docs, size=min(n_visits, len(local_docs)),
                                   replace=False, p=probs[:len(local_docs)])

        month_start = start_date + timedelta(days=30*month)
        for doc_id in visited:
            visit_date = month_start + timedelta(days=np.random.randint(0,28))
            product = np.random.choice(PRODUCTS)
            duration = np.random.randint(5, 25)  # minutes
            visit_records.append({
                "visit_id":    f"V{str(visit_id).zfill(6)}",
                "rep_id":      rep["rep_id"],
                "doctor_id":   doc_id,
                "visit_date":  visit_date.strftime("%Y-%m-%d"),
                "month":       visit_date.month,
                "quarter":     (visit_date.month - 1)//3 + 1,
                "product":     product,
                "duration_min": duration,
                "samples_left": np.random.randint(0, 5),
            })
            visit_id += 1

visits = pd.DataFrame(visit_records)

# ── 5. PRESCRIPTIONS ──────────────────────────────────────────────────────────
# Prescriptions driven by: visit frequency × doctor potential × product fit
presc_records = []
presc_id = 1

# Product-specialty affinity
affinity = {
    ("CardioMax",  "Cardiologist"):    0.80,
    ("CardioMax",  "Internist"):       0.40,
    ("CardioMax",  "General Physician"):0.25,
    ("DiabeCure",  "Diabetologist"):   0.85,
    ("DiabeCure",  "General Physician"):0.35,
    ("DiabeCure",  "Internist"):       0.30,
    ("NeuroCalm",  "Neurologist"):     0.80,
    ("NeuroCalm",  "General Physician"):0.20,
}

for _, doc in doctors.iterrows():
    doc_visits = visits[visits["doctor_id"] == doc["doctor_id"]]
    if doc_visits.empty:
        continue

    pot_multiplier = {"High": 1.5, "Medium": 1.0, "Low": 0.4}[doc["prescribing_potential"]]

    for month in range(1, N_MONTHS+1):
        month_visits = doc_visits[doc_visits["month"] == month]
        for product in PRODUCTS:
            prod_visits = month_visits[month_visits["product"] == product]
            if prod_visits.empty:
                continue

            base_prob = affinity.get((product, doc["specialty"]), 0.15)
            freq_boost = min(len(prod_visits) * 0.10, 0.30)
            final_prob = min(base_prob + freq_boost, 0.95) * pot_multiplier * 0.8

            if np.random.random() < final_prob:
                units = int(np.random.randint(5, 50) * pot_multiplier)
                price = {"CardioMax": 850, "DiabeCure": 620, "NeuroCalm": 1100}[product]
                presc_records.append({
                    "prescription_id": f"P{str(presc_id).zfill(6)}",
                    "doctor_id":       doc["doctor_id"],
                    "territory_id":    doc["territory_id"],
                    "product":         product,
                    "month":           month,
                    "quarter":         (month-1)//3 + 1,
                    "units_prescribed": units,
                    "revenue":         units * price,
                    "visit_count":     len(prod_visits),
                })
                presc_id += 1

prescriptions = pd.DataFrame(presc_records)

# ── SAVE ──────────────────────────────────────────────────────────────────────
territories.to_csv(f"{OUTPUT_DIR}/territories.csv",   index=False)
reps.to_csv(       f"{OUTPUT_DIR}/reps.csv",           index=False)
doctors.to_csv(    f"{OUTPUT_DIR}/doctors.csv",        index=False)
visits.to_csv(     f"{OUTPUT_DIR}/visits.csv",         index=False)
prescriptions.to_csv(f"{OUTPUT_DIR}/prescriptions.csv", index=False)

print("✅ Data generated successfully!")
print(f"   Territories : {len(territories)}")
print(f"   Reps        : {len(reps)}")
print(f"   Doctors     : {len(doctors)}")
print(f"   Visits      : {len(visits)}")
print(f"   Prescriptions: {len(prescriptions)}")
