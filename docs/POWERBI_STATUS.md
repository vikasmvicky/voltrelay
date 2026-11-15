# Power BI / Tableau — status and build guide

## Status: read this first

**No `.pbix` file exists.** Power BI Desktop is a Windows application and cannot run in this
Linux environment, so I could not create, open, or test a report file. Nothing in this package
claims otherwise.

What **does** exist and is verified:

| Component | File | Verified |
|---|---|---|
| Star schema, 6 dimensions + 4 facts | `model/*.csv` | Reconciliation to the notebook: **0 mismatches** (`reports/star_measures.txt`) |
| 64 DAX measures, grouped and commented | `model/DAX_Measures.dax` | Each measure's value recomputed from the CSVs by `scripts/verify_star.py` |
| Typed Power Query loader | `model/PowerQuery_M.txt` | Not executed in Power BI — validated only as text |
| Column dictionary (156 columns) | `model/_column_dictionary.csv` | Generated from the actual exports |
| Model design, ERD, relationships, Tableau notes | `model/README_powerbi.md` | — |
| Regeneration + verification | `scripts/build_star_schema.py`, `scripts/verify_star.py` | Both run clean |

So: the **data model is done and checked**, the **report canvas is not**. Building the canvas
is 20–30 minutes of clicking, and the page blueprint below tells you exactly what to place.

---

## The 20-minute build

1. **Get Data → Blank query → Advanced Editor**, paste `model/PowerQuery_M.txt`, set the one
   `MODEL_PATH` line to your `model` folder. Create each query in turn (they depend on
   `fnLoadCsv`).
2. Skip `FactStationHour` unless you want thermal drill-through — it is 1.49 M rows and is the
   only table that makes the model large.
3. Create the **12 relationships** listed in `model/README_powerbi.md` §2. Single direction,
   one-to-many. Hide the columns in its "hiding checklist" — this prevents the two classic
   mistakes (ambiguous `city` path, double date dimension).
4. Select `DimDate` → **Mark as date table** → `date`.
5. Paste `model/DAX_Measures.dax` in sections (**Modelling → New measure**).
6. Build the four pages below.

---

## Page blueprint

### Page 1 — Executive (what leadership sees)

| Visual | Type | Fields |
|---|---|---|
| Success rate over time | Line | `DimDate[month_start]` × `[Success Rate]`, reference line at network average |
| KPI cards (4) | Card | `[Success Rate]`, `[Completed Swaps]`, `[Gross Margin]`, `[Churn Rate (2m)]` |
| Failure mix | 100% stacked column | `DimDate[month_start]` × four failure measures |
| Top/bottom stations | Bar | `DimStation[station_label]` × `[Success Rate]`, filter to stations with >1,000 attempts |

Slicers: `DimDate[year_month]`, `DimCity[city]`.

### Page 2 — Thermal story

| Visual | Type | Fields |
|---|---|---|
| Heat vs cool day | Clustered column | `FactStationDay[heat_alert]` × `[Success Rate]` |
| Cabinet temperature bands | Column | temp band (create a calculated column on `cabinet_temp_avg`) × `[Success Rate]` |
| Hot-hour share | Card | `[% Attempts in Hot Hours]` |
| Cooling target list | Table | `DimStation[station_label]`, `[Hot-Hour Attempts]`, `[Heat Gap (pp)]` |

**Say this in the report:** the effect survives station fixed effects in the notebook
(OR 3.07–3.82). A Power BI visual cannot show that — it is not a causal estimate, it is a
description. Do not relabel a bar chart as a regression result.

### Page 3 — Riders and churn

| Visual | Type | Fields |
|---|---|---|
| Active riders | Line | `DimDate[month_start]` × `[Active Riders]` |
| Churn by city | Bar | `DimCity[city]` × `[Churn Rate (2m)]` |
| Rider failure experience | Scatter | `[Rider Failure Rate]` vs `[Churn Rate (2m)]` by city |
| Retention by partner | Matrix | `DimPartner[partner_name]` × `[Churn Rate (2m)]`, `[Swaps per Active Rider]` |

### Page 4 — Margin and action

| Visual | Type | Fields |
|---|---|---|
| Contribution by station | Waterfall or bar | `DimStation[station_label]` × `[Contribution]` |
| Discount trend | Line | `DimDate[month_start]` × `[Discount Rate]` |
| Loss-making stations | Card + table | `[Loss-Making Stations]`, then the station rows |
| Action plan | Table | Hard-coded 7 rows from `reports/key_findings.json` (`priorities[]`), with `₹/year` — this is a text table, not a data visual |

---

## Honest limitations to carry into the report

- **Contribution, not profit.** `[Contribution]` = gross margin minus station rent and
  maintenance. No capex, no rider acquisition cost, no support cost, no depreciation.
- **Fixed cost is per station-month**, so the first and last months understate contribution by
  up to half a month's rent.
- **`DimBattery` is a snapshot** and relates only to `FactTicket`, so battery slicers do not
  respond to the date slicer. That is correct behaviour, not a broken relationship.
- **The stockout-churn cut is deliberately absent.** It runs backwards (5.75% vs 8.82%) because
  stockout exposure proxies for activity. Documented in `DAX_Measures.dax` under
  `DELIBERATE OMISSION`.
- **The pricing DiD fails its parallel-trends test.** If you put a pricing visual on a page, say
  so; do not present −8.2% as a clean causal number.

---

## Tableau instead?

Same CSVs, same relationships. Tableau cannot execute DAX, so rebuild the measures as
calculated fields — the five that matter are listed in `model/README_powerbi.md` §5. Critically:
use `SUM([swaps]) / SUM([attempts])`, never `AVG` of a per-row ratio; averaging ratios is the
single most common error on this dataset and it will overstate success rate.
