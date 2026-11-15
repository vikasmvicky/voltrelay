# VoltRelay — Battery-Swap Network Diagnostic

Hackathon submission: an evidence-based diagnosis of network performance, service failures,
rider churn and margin erosion across 3.88M swap attempts (Jan 2024 – Jun 2025, India).

## What to open

| Deliverable | File | What it is |
|---|---|---|
| **1. Colab notebook** | [`VoltRelay_Analysis.ipynb`](VoltRelay_Analysis.ipynb) | 47 code cells, runs top-to-bottom, 17 figures, incl. a robustness section. Executed copy with all outputs: [`VoltRelay_Analysis_COMPLETED.ipynb`](VoltRelay_Analysis_COMPLETED.ipynb) |
| **2. Analysis report** | [`reports/ANALYSIS_REPORT.md`](reports/ANALYSIS_REPORT.md) | Problem understanding, approach, insights, findings, recommendations, limitations |
| **3. Video script** | [`reports/VIDEO_SCRIPT.md`](reports/VIDEO_SCRIPT.md) | 3:00 script in the required order, with slide and production notes |
| **Dashboard** | [`dashboard/VoltRelay_Dashboard.html`](dashboard/VoltRelay_Dashboard.html) | Self-contained interactive dashboard — 8 tabs, KPI cards, 17 charts, robustness tab, action plan. No internet needed |
| **Power BI / Tableau model** | [`model/`](model/README_powerbi.md) | Star schema export — 6 dimensions, 4 facts, 54 MB of CSV, 64 DAX measures, typed Power Query loader, column dictionary, reconciliation report |

Supporting: `reports/key_findings.json` (every number in the report and dashboard, written by the
notebook), `reports/data_profile.txt`, `reports/explore.txt`, `figures/` (16 PNGs).

## Requirements coverage

| Requirement | Where |
|---|---|
| Understanding the business problem and dataset | Report §2 · Notebook §2 (schema, keys, date coverage, null structure) |
| Cleaning, transforming, preparing | Report §3 · Notebook §3 — 6-step ledger with row counts, plus **3 documented traps** |
| Exploring patterns, trends, relationships | Notebook §4–7 · Report §4 |
| Quantitative and statistical analysis | Binomial z-tests on 152 stations; cell-aggregated weighted binomial GLM (odds ratios, 95% CIs) **plus a 152-dummy station fixed-effects model**; rider-month panel (116,907 obs) with rider-clustered bootstrap CI; two difference-in-differences designs with parallel-trends tests |
| Meaningful visualizations **and dashboards** | 17 publication figures + `dashboard/VoltRelay_Dashboard.html` (8 tabs) |
| Key insights and actionable recommendations | Report §5–6 · Notebook §10 — 7 initiatives sized in swaps and ₹/year, plus a 12-station cooling target list |
| Presenting the analysis | `reports/VIDEO_SCRIPT.md` + report |

## Headline findings

- Success rate is **95.66% ± 0.1pp** for eleven of eighteen months, and **90.15% / 91.69%** in the two
  pre-monsoon summers. Growth (+191% swaps) is not the cause.
- **Heat is the primary driver**: heat-day OR **2.74 → 1.65** once cabinet temperature is controlled;
  cabinet >40 °C carries **OR 3.07–3.82 within the same station** (152 fixed effects), so it is not a
  station-quality artefact.
- **Charged stock is a symptom, not the cause**: marginal gap 88.5% vs 94.6%, but **OR 1.09** under
  controls, and adding stock does not attenuate the heat effect at all.
- **Gen1 cabinets in Jaipur/Delhi** collapse to 79–88% every April–June (OR 1.33).
- **Kyron packs degrade 3.25× faster** (9.53 vs 2.93 SOH pts per 100 deliveries); all 1,438 retirements
  dated 15 Jun 2025 removed **21.4%** of active packs in one day.
- **Churn**: the naive test says failures *retain* riders (51.4% churn at zero failures) — an activity
  artefact. The rider-month panel shows a monotonic 2.5% → 39.4% gradient.
- **Margin**: contribution ₹26.70/swap, but **23 of 152 stations are loss-making** (−₹2.37 L/month) and
  one contract amended 12% → 28% leaks **₹4.90 L/month**.
- **≈₹1.17 crore/year** of gross margin identified across 7 initiatives — the biggest reliability
  lever is the **Gen1 retrofit**, not thermal cooling, once the thermal prize is sized within-station.

## Running it

**In Colab.** Upload the `.ipynb`, then point it at the dataset (it auto-detects common locations):

```python
from google.colab import drive; drive.mount('/content/drive')
import os
os.environ["VOLTRELAY_DATA"] = "/content/drive/MyDrive/Hackathon Data Set | Gradient"
```

Then **Runtime → Run all**. Needs only pandas, numpy, matplotlib and scipy — all preinstalled in Colab.
Expect ~3 minutes and ~2.5 GB peak RAM.

**Locally.**

```bash
python -m pip install pandas numpy matplotlib scipy jupytext nbconvert ipykernel
jupyter nbconvert --to notebook --execute VoltRelay_Analysis.ipynb --output VoltRelay_Analysis_COMPLETED.ipynb
python scripts/build_dashboard.py     # rebuild the dashboard from figures + key_findings.json
```

The notebook writes `reports/key_findings.json`; the report and dashboard both read it, so numbers in
all three deliverables cannot drift apart.

**Data.** The eight CSVs go in `data/Hackathon Data Set | Gradient/`. They are not committed — 808 MB,
and `.gitignore` excludes them.

## Method notes a reviewer should know

Three traps were found and neutralised rather than stepped in:

1. **Survivorship in battery-out data.** Failed swaps have no `battery_out_id`, so "success by
   out-pack SOH" returns 100% in every band. Battery effects are measured on the *returned* pack.
2. **Templated ticket text.** 44,000 tickets hold 89 distinct comments, each mapping to one category —
   text mining would only rediscover the category. No NLP is claimed.
3. **CSAT missing not-at-random.** CSAT exists only for resolved tickets (15,129 of 44,000).

Two other honest limitations: `attempt_seq` is identically 1 in all 3.88M rows (no retry chains can be
reconstructed), and `payment_mode` is `partner_invoice` for every row including independent riders
(billing attribution is unreliable, so revenue is read from `amount_charged_inr`).

The pricing-pilot difference-in-differences **fails its parallel-trends test** (+36.9% vs +25.8% pre-growth).
That is reported in the notebook, the report and the dashboard rather than hidden; the log-scale DiD
(−8.2% [−13.5%, −2.5%]) is given as the more defensible estimate.

**What changed after the first draft** (notebook §11, dashboard "Robustness" tab):

| Claim | First version | After testing |
|---|---|---|
| Thermal prize | ₹18.6 L/yr (whole seasonal gap credited to heat) | **₹5.8 L/yr** — within-station gap is 5.8pp over 481,106 hot-hour attempts, 70% capture |
| Heat effect robustness | cell-level model only | **survives 152 station fixed effects** (OR 3.07–3.82) |
| Kyron | 3.25× faster per delivery | **holds after age + usage controls** (−8.66pp, t = −58.7, and Kyron packs are *younger*) |
| Churn gap | +4.8pp, no interval | **+4.8pp [+4.4, +5.1]** rider-clustered bootstrap |
| Recommendations order | cooling first | **discount → stations → Gen1 → queue → cooling** |
| Unit error | thermal total labelled ₹/month (18× overstated) | derived from the data, not the row title |

---

## Power BI / Tableau model

The dashboard is HTML so it opens anywhere with no licence, but the same analysis is exported
as a proper star schema for anyone who wants to rebuild it in a BI tool:
[`model/README_powerbi.md`](model/README_powerbi.md).

- **Grain**: station-day (61,994 rows) for reliability and margin, rider-month (140,575) for
  churn, plus ticket and optional hourly-telemetry facts. The 3.88 M-event log is *not* loaded
  as a fact — every measure here is a ratio of sums, so pre-aggregation is exact and 98% smaller.
- **64 DAX measures** in [`model/DAX_Measures.dax`](model/DAX_Measures.dax) + Tableau calculated-field
  equivalents, typed Power Query in [`model/PowerQuery_M.txt`](model/PowerQuery_M.txt).
- **Reconciled**: `scripts/verify_star.py` recomputes every measure from the exported CSVs and
  diffs it against the notebook — 3,877,013 attempts, 94.04% success, ₹16.20 Cr gross margin,
  ₹44.45 → ₹26.70 per swap, 23 loss-making stations, **0 mismatches**
  ([report](reports/star_measures.txt)).
