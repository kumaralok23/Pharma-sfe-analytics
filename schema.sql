-- ============================================================
-- PHARMA SFE ANALYTICS — DATABASE SCHEMA & ANALYTICAL QUERIES
-- Compatible with: MySQL 8+ / PostgreSQL 13+
-- ============================================================

-- ─────────────────────────────────────────────────────────────
-- SECTION 1: SCHEMA CREATION
-- ─────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS territories (
    territory_id       VARCHAR(5)   PRIMARY KEY,
    territory_name     VARCHAR(50),
    state              VARCHAR(50),
    region             VARCHAR(20),
    market_potential   BIGINT
);

CREATE TABLE IF NOT EXISTS reps (
    rep_id             VARCHAR(5)   PRIMARY KEY,
    rep_name           VARCHAR(100),
    territory_id       VARCHAR(5)   REFERENCES territories(territory_id),
    experience_yrs     INT,
    target_calls       INT
);

CREATE TABLE IF NOT EXISTS doctors (
    doctor_id              VARCHAR(6)   PRIMARY KEY,
    doctor_name            VARCHAR(100),
    specialty              VARCHAR(50),
    territory_id           VARCHAR(5)   REFERENCES territories(territory_id),
    prescribing_potential  VARCHAR(10),
    potential_score        INT,
    years_in_practice      INT
);

CREATE TABLE IF NOT EXISTS visits (
    visit_id       VARCHAR(8)   PRIMARY KEY,
    rep_id         VARCHAR(5)   REFERENCES reps(rep_id),
    doctor_id      VARCHAR(6)   REFERENCES doctors(doctor_id),
    visit_date     DATE,
    month          INT,
    quarter        INT,
    product        VARCHAR(30),
    duration_min   INT,
    samples_left   INT
);

CREATE TABLE IF NOT EXISTS prescriptions (
    prescription_id    VARCHAR(8)   PRIMARY KEY,
    doctor_id          VARCHAR(6)   REFERENCES doctors(doctor_id),
    territory_id       VARCHAR(5)   REFERENCES territories(territory_id),
    product            VARCHAR(30),
    month              INT,
    quarter            INT,
    units_prescribed   INT,
    revenue            BIGINT,
    visit_count        INT
);


-- ─────────────────────────────────────────────────────────────
-- SECTION 2: CORE KPI QUERIES
-- ─────────────────────────────────────────────────────────────

-- KPI 1: Rep Performance Scorecard
-- Measures: actual calls vs target, prescriptions generated, revenue per call
SELECT
    r.rep_id,
    r.rep_name,
    t.territory_name,
    r.target_calls,
    COUNT(DISTINCT v.visit_id)                          AS actual_calls,
    ROUND(COUNT(DISTINCT v.visit_id) * 100.0 / r.target_calls, 1) AS call_achievement_pct,
    COUNT(DISTINCT v.doctor_id)                         AS unique_doctors_visited,
    COALESCE(SUM(p.revenue), 0)                         AS total_revenue_generated,
    ROUND(COALESCE(SUM(p.revenue), 0) * 1.0 /
          NULLIF(COUNT(DISTINCT v.visit_id), 0), 0)     AS revenue_per_call
FROM reps r
JOIN territories t          ON r.territory_id = t.territory_id
LEFT JOIN visits v          ON r.rep_id = v.rep_id
LEFT JOIN prescriptions p   ON v.doctor_id = p.doctor_id
                            AND v.product   = p.product
                            AND v.month     = p.month
GROUP BY r.rep_id, r.rep_name, t.territory_name, r.target_calls
ORDER BY total_revenue_generated DESC;


-- KPI 2: Call Efficiency — Are reps calling on the right doctors?
-- Flags reps spending >40% calls on Low-potential doctors
SELECT
    r.rep_id,
    r.rep_name,
    d.prescribing_potential,
    COUNT(*) AS call_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY r.rep_id), 1) AS pct_of_calls
FROM visits v
JOIN reps    r ON v.rep_id    = r.rep_id
JOIN doctors d ON v.doctor_id = d.doctor_id
GROUP BY r.rep_id, r.rep_name, d.prescribing_potential
ORDER BY r.rep_id, d.prescribing_potential;


-- KPI 3: Reach & Frequency Analysis
-- Reach = % of territory doctors visited; Frequency = avg visits per doctor
SELECT
    r.rep_id,
    r.rep_name,
    t.territory_name,
    COUNT(DISTINCT d_all.doctor_id)                       AS total_docs_in_territory,
    COUNT(DISTINCT v.doctor_id)                           AS docs_visited,
    ROUND(COUNT(DISTINCT v.doctor_id) * 100.0 /
          NULLIF(COUNT(DISTINCT d_all.doctor_id), 0), 1) AS reach_pct,
    ROUND(COUNT(v.visit_id) * 1.0 /
          NULLIF(COUNT(DISTINCT v.doctor_id), 0), 1)     AS avg_visit_frequency
FROM reps r
JOIN territories t              ON r.territory_id = t.territory_id
LEFT JOIN doctors d_all         ON d_all.territory_id = r.territory_id
LEFT JOIN visits v              ON v.rep_id = r.rep_id
GROUP BY r.rep_id, r.rep_name, t.territory_name
ORDER BY reach_pct DESC;


-- KPI 4: Product Performance by Territory (Revenue + Market Share Proxy)
SELECT
    t.territory_name,
    t.region,
    p.product,
    SUM(p.units_prescribed)   AS total_units,
    SUM(p.revenue)            AS total_revenue,
    ROUND(SUM(p.revenue) * 100.0 /
          SUM(SUM(p.revenue)) OVER (PARTITION BY t.territory_id), 1) AS revenue_share_pct
FROM prescriptions p
JOIN territories t ON p.territory_id = t.territory_id
GROUP BY t.territory_id, t.territory_name, t.region, p.product
ORDER BY t.territory_name, total_revenue DESC;


-- KPI 5: Prescribing Trend — Monthly Revenue by Product (for trend charts)
SELECT
    month,
    product,
    SUM(revenue)          AS monthly_revenue,
    SUM(units_prescribed) AS monthly_units,
    COUNT(DISTINCT doctor_id) AS prescribing_doctors
FROM prescriptions
GROUP BY month, product
ORDER BY month, product;


-- KPI 6: Doctor Segmentation — Visit Investment vs Return
-- Identifies over-called low-value and under-called high-value doctors
SELECT
    d.doctor_id,
    d.doctor_name,
    d.specialty,
    d.prescribing_potential,
    d.potential_score,
    COUNT(v.visit_id)              AS total_visits_received,
    COALESCE(SUM(p.revenue), 0)    AS revenue_generated,
    CASE
        WHEN d.prescribing_potential = 'High'   AND COUNT(v.visit_id) < 8  THEN 'Under-called High Value'
        WHEN d.prescribing_potential = 'Low'    AND COUNT(v.visit_id) > 6  THEN 'Over-called Low Value'
        WHEN d.prescribing_potential = 'Medium' AND COUNT(v.visit_id) >= 6 THEN 'Well Covered'
        ELSE 'Standard Coverage'
    END AS coverage_flag
FROM doctors d
LEFT JOIN visits v        ON d.doctor_id = v.doctor_id
LEFT JOIN prescriptions p ON d.doctor_id = p.doctor_id
GROUP BY d.doctor_id, d.doctor_name, d.specialty,
         d.prescribing_potential, d.potential_score
ORDER BY revenue_generated DESC;


-- KPI 7: Territory ROI — Revenue vs Market Potential
SELECT
    t.territory_id,
    t.territory_name,
    t.state,
    t.region,
    t.market_potential,
    COALESCE(SUM(p.revenue), 0)   AS realized_revenue,
    ROUND(COALESCE(SUM(p.revenue), 0) * 100.0 /
          t.market_potential, 2)  AS market_capture_pct,
    COUNT(DISTINCT r.rep_id)      AS rep_count
FROM territories t
LEFT JOIN reps r           ON t.territory_id = r.territory_id
LEFT JOIN prescriptions p  ON t.territory_id = p.territory_id
GROUP BY t.territory_id, t.territory_name, t.state, t.region, t.market_potential
ORDER BY market_capture_pct DESC;


-- ─────────────────────────────────────────────────────────────
-- SECTION 3: OPTIMIZATION INSIGHTS
-- ─────────────────────────────────────────────────────────────

-- Insight 1: Identify wasted calls (Low potential doctors with high visit count)
SELECT
    r.rep_name,
    d.doctor_name,
    d.prescribing_potential,
    COUNT(v.visit_id)          AS visits_made,
    COALESCE(SUM(p.revenue),0) AS revenue_from_doctor,
    CASE WHEN COALESCE(SUM(p.revenue),0) = 0 THEN 'ZERO RETURN' ELSE 'Some Return' END AS roi_flag
FROM visits v
JOIN reps    r ON v.rep_id    = r.rep_id
JOIN doctors d ON v.doctor_id = d.doctor_id
LEFT JOIN prescriptions p ON d.doctor_id = p.doctor_id
WHERE d.prescribing_potential = 'Low'
GROUP BY r.rep_name, d.doctor_name, d.prescribing_potential
HAVING COUNT(v.visit_id) >= 5
ORDER BY visits_made DESC
LIMIT 20;


-- Insight 2: High-value doctors with NO visits (untapped opportunity)
SELECT
    d.doctor_id,
    d.doctor_name,
    d.specialty,
    d.prescribing_potential,
    d.potential_score,
    t.territory_name
FROM doctors d
JOIN territories t ON d.territory_id = t.territory_id
LEFT JOIN visits v ON d.doctor_id = v.doctor_id
WHERE d.prescribing_potential = 'High'
  AND v.visit_id IS NULL
ORDER BY d.potential_score DESC;
