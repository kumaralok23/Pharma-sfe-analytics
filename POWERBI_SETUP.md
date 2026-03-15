# Power BI Setup Guide — Pharma SFE Analytics Dashboard
# Follow these steps to build the full Power BI dashboard in ~15 minutes

## STEP 1: LOAD DATA
# Open Power BI Desktop → Get Data → Text/CSV → load all 7 files:
#   territories.csv, reps.csv, doctors.csv, visits.csv,
#   prescriptions.csv, rep_performance.csv, doctor_segments.csv


## STEP 2: DATA MODEL (Relationships)
# Go to Model view and create these relationships:
#
#   reps[territory_id]          → territories[territory_id]   (Many-to-One)
#   doctors[territory_id]       → territories[territory_id]   (Many-to-One)
#   visits[rep_id]              → reps[rep_id]                (Many-to-One)
#   visits[doctor_id]           → doctors[doctor_id]          (Many-to-One)
#   prescriptions[territory_id] → territories[territory_id]   (Many-to-One)
#   prescriptions[doctor_id]    → doctors[doctor_id]          (Many-to-One)
#   rep_performance[rep_id]     → reps[rep_id]                (Many-to-One)
#   doctor_segments[doctor_id]  → doctors[doctor_id]          (Many-to-One)


## STEP 3: DAX MEASURES
# In the prescriptions table, create a new "Measures" table (Enter Data → blank table named "Measures")
# Then add these DAX measures:

Total Revenue = SUM(prescriptions[revenue])

Total Units = SUM(prescriptions[units_prescribed])

Total Visits = COUNTROWS(visits)

Unique Doctors Visited = DISTINCTCOUNT(visits[doctor_id])

Avg Efficiency Score = AVERAGE(rep_performance[efficiency_score])

Market Capture % =
DIVIDE(
    SUM(prescriptions[revenue]),
    SUM(territories[market_potential]),
    0
) * 100

Revenue per Visit =
DIVIDE(
    [Total Revenue],
    [Total Visits],
    0
)

High Potential Call % =
DIVIDE(
    CALCULATE(COUNTROWS(visits), RELATED(doctors[prescribing_potential]) = "High"),
    [Total Visits],
    0
) * 100

QoQ Revenue Growth =
VAR CurrentQ = MAX(prescriptions[quarter])
VAR PrevQRev =
    CALCULATE(
        [Total Revenue],
        prescriptions[quarter] = CurrentQ - 1
    )
RETURN
    DIVIDE([Total Revenue] - PrevQRev, PrevQRev, 0) * 100

Wasted Calls (Low Potential) =
CALCULATE(
    COUNTROWS(visits),
    RELATED(doctors[prescribing_potential]) = "Low"
)

Rep Efficiency Score = AVERAGE(rep_performance[efficiency_score])


## STEP 4: BUILD THESE 6 VISUALS

### PAGE 1: Executive Overview
#
# 1. KPI CARDS (top row) — 5 cards:
#    Card visual → Field: [Total Revenue]       → Format: ₹ currency, Title: "Total Revenue"
#    Card visual → Field: [Total Units]          → Title: "Units Prescribed"
#    Card visual → Field: [Total Visits]         → Title: "Field Visits"
#    Card visual → Field: [Unique Doctors Visited] → Title: "Doctors Reached"
#    Card visual → Field: [Avg Efficiency Score] → Title: "Avg Rep Efficiency"
#
# 2. LINE CHART — Monthly Revenue Trend
#    X-axis: prescriptions[month]
#    Y-axis: [Total Revenue]
#    Legend: prescriptions[product]
#    Title: "Monthly Revenue Trend by Product"
#
# 3. DONUT CHART — Revenue by Product
#    Values: [Total Revenue]
#    Legend: prescriptions[product]
#    Title: "Revenue Split by Product"
#
# 4. CLUSTERED BAR — Quarterly Revenue by Product
#    X-axis: prescriptions[quarter]
#    Y-axis: [Total Revenue]
#    Legend: prescriptions[product]
#    Title: "Quarterly Revenue by Product"
#
# 5. SLICER — Region (territories[region])
# 6. SLICER — Product (prescriptions[product])
# 7. SLICER — Quarter (prescriptions[quarter])


### PAGE 2: Rep Performance
#
# 1. TABLE — Rep Scorecard (from rep_performance table)
#    Columns: rep_name, efficiency_score, high_pct, low_pct,
#             total_calls, call_achievement_pct, total_revenue
#    → Conditional formatting on efficiency_score:
#      Green ≥ 1.8, Yellow 1.4–1.8, Red < 1.4
#
# 2. BAR CHART — Efficiency Score by Rep
#    Y-axis: rep_performance[rep_name]
#    X-axis: [Rep Efficiency Score]
#    Sort: descending
#    Add reference line at median
#    Title: "Rep Call Efficiency Score"
#
# 3. STACKED BAR — Call Distribution by Potential
#    Y-axis: reps[rep_name]
#    X-axis: COUNTROWS(visits)
#    Legend: doctors[prescribing_potential]
#    Title: "Call Distribution by Doctor Potential"
#
# 4. SCATTER CHART — Efficiency vs Revenue
#    X-axis: [Rep Efficiency Score]
#    Y-axis: [Total Revenue]
#    Size: rep_performance[total_calls]
#    Details: reps[rep_name]
#    Title: "Revenue vs Efficiency (Bubble = Call Volume)"


### PAGE 3: Doctor Segmentation (ML)
#
# 1. SCATTER CHART — ML Clusters
#    X-axis: doctor_segments[total_visits]
#    Y-axis: doctor_segments[total_revenue]
#    Legend: doctor_segments[segment]
#    Size: doctor_segments[potential_score]
#    Title: "Doctor Segmentation — K-Means Clusters"
#
# 2. CLUSTERED BAR — Doctors per Segment
#    Y-axis: doctor_segments[segment]
#    X-axis: COUNTROWS(doctor_segments)
#    Title: "Doctor Count by Segment"
#
# 3. TABLE — Segment Summary
#    Columns: segment, COUNT(doctor_id), AVG(total_visits),
#             AVG(total_revenue), AVG(potential_score)
#
# 4. TEXT BOX — Segment Recommendations (add manually):
#    🟢 High Value – Well Covered: Maintain coverage
#    🔵 High Value – Under-visited: Increase visit priority
#    🔴 Low Value – Over-visited: Reduce, redirect calls
#    🟡 Low Value – Low Coverage: Monitor only


### PAGE 4: Territory Analysis
#
# 1. BAR CHART — Market Capture % by Territory
#    Y-axis: territories[territory_name]
#    X-axis: [Market Capture %]
#    Sort: descending
#    Title: "Market Capture % by Territory"
#
# 2. SCATTER — Revenue vs Market Potential
#    X-axis: territories[market_potential]
#    Y-axis: [Total Revenue]
#    Size: [Market Capture %]
#    Details: territories[territory_name]
#    Title: "Revenue vs Market Potential"
#
# 3. STACKED BAR — Product Mix by Territory
#    X-axis: territories[territory_name]
#    Y-axis: [Total Revenue]
#    Legend: prescriptions[product]
#    Title: "Product Revenue Mix by Territory"
#
# 4. TABLE — Territory Scorecard
#    Columns: territory_name, region, market_potential,
#             [Total Revenue], [Market Capture %]
#    Conditional format: Market Capture % → Red-Yellow-Green scale


## STEP 5: FORMATTING (ZS-style professional look)
#
# Theme: Apply a custom theme — go to View → Themes → Customize
#   Primary color:    #1F4E79  (dark blue)
#   Secondary color:  #2E86C1  (mid blue)
#   Accent colors:    #2ECC71 (green), #E74C3C (red), #F39C12 (amber)
#   Background:       #F8FAFC (off-white)
#   Font:             Segoe UI
#
# Page background: Set all pages to #F8FAFC
# Visual borders: Light shadow, rounded corners (8px)
# Title font size: 13px bold, color #1F4E79
# Value font size: 28px bold for KPI cards


## STEP 6: PUBLISH (Optional — for live link)
# File → Publish → Publish to Power BI Service (free account)
# Share the URL in your resume / portfolio / GitHub README


## POWER QUERY: CALCULATED COLUMNS TO ADD
# In Power Query Editor → Add Column → Custom Column:

# In visits table:
# Column: "Visit_Month_Name"
# Formula: = Date.MonthName(Date.From([visit_date]))

# In prescriptions table:
# Column: "Quarter_Label"
# Formula: = "Q" & Text.From([quarter])
