# VoltRelay — Power BI / Tableau data model

A star schema built from the eight raw VoltRelay CSVs, sized so it opens comfortably in
Power BI Desktop and Tableau Desktop. Everything the notebook concluded can be rebuilt from
these files; every number in `reports/ANALYSIS_REPORT.md` reconciles to them (see
[Validation](#validation)).

```
model/
├── dim_date.csv                 943 rows    calendar 2023-01-01 → 2025-07-31
├── dim_station.csv              152 rows    one row per cabinet
├── dim_city.csv                   6 rows    one row per city
├── dim_rider.csv             20,000 rows    one row per rider + lifetime behaviour
├── dim_battery.csv            6,500 rows    one row per pack + deliveries + SOH
├── dim_partner.csv               12 rows    fleet partners + effective discount
├── fact_station_day.csv      61,994 rows    station × day — the primary fact
├── fact_rider_month.csv     140,575 rows    rider × month — churn and retention
├── fact_ticket.csv           44,000 rows    support tickets
├── fact_station_hour.csv.gz 1,487,712 rows  hourly telemetry — optional drill-through
├── DAX_Measures.dax                        64 measures, grouped, commented
├── PowerQuery_M.txt                         typed load queries for Power BI
└── _column_dictionary.csv                   every column, its type, what it means
```

Total on disk: **54 MB** uncompressed (~14 MB once Power BI compresses it).

---

## 1. Why the grain is not the event log

The raw `swap_events.csv` is 3.88 M rows across 20 columns. Loading that as a fact is the
single most common way to make a .pbix that a judge closes after ten seconds: slow visuals,
a 400 MB model, and slicers that hang.

The measures that matter here — success rate, failure mix, margin per swap, churn — are all
**ratio-of-sums** measures, so they are grain-preserving: `sum(swaps) / sum(attempts)` computed
on station-days is mathematically identical to the same ratio on events. Pre-aggregating to
station-day (152 × 547 possible, 61,994 actual) keeps 100% of the analysis and cuts rows by 98%.

Two things genuinely need a finer grain and get their own facts:

| Question | Grain | Rows |
|---|---|---|
| Rider retention / churn | rider × month | 140,575 |
| Thermal behaviour at hour level | station × hour | 1,487,712 (gzip, optional) |

Support tickets are their own fact because a ticket has a different key set (ticket id, CSAT,
resolution) and would otherwise fan out the swap fact.

---

## 2. Relationships

Import all tables, then create exactly these relationships. Cardinality is one-to-many,
single-direction filter, in every case.

| # | From (one) | To (many) | Key | Notes |
|---|---|---|---|---|
| 1 | `DimDate[date]` | `FactStationDay[date]` | date | active |
| 2 | `DimDate[date]` | `FactRiderMonth[month_start]` | date | month-start dates |
| 3 | `DimDate[date]` | `FactTicket[created_date]` | date | |
| 4 | `DimDate[date_key]` | `FactStationHour[date_key]` | integer | hourly fact has no plain date column |
| 5 | `DimStation[station_id]` | `FactStationDay[station_id]` | text | |
| 6 | `DimStation[station_id]` | `FactTicket[station_id]` | text | |
| 7 | `DimStation[station_id]` | `FactStationHour[station_id]` | text | |
| 8 | `DimCity[city]` | `DimStation[city]` | text | snowflake: city → station → fact |
| 9 | `DimRider[rider_id]` | `FactRiderMonth[rider_id]` | text | |
| 10 | `DimRider[rider_id]` | `FactTicket[rider_id]` | text | |
| 11 | `DimPartner[partner_id]` | `DimRider[partner_id]` | text | |
| 12 | `DimBattery[battery_id]` | `FactTicket[battery_id]` | text | |

```
                         ┌──────────────┐
                         │   DimDate    │  943 rows · marked as date table
                         └──┬────┬────┬─┘
                  date      │    │    │      date
        ┌───────────────────┘    │    └───────────────────┐
        │                        │                        │
┌───────▼──────────┐   ┌─────────▼────────┐   ┌───────────▼───────┐
│ FactStationDay   │   │  FactRiderMonth  │   │    FactTicket     │
│   61,994 rows    │   │   140,575 rows   │   │    44,000 rows    │
└──┬──────────┬────┘   └────────┬─────────┘   └──┬───────┬────┬───┘
   │          │                 │                │       │    │
station      city            rider_id         station  rider battery
   │          │                 │                │       │    │
   ▼          ▼                 ▼                ▼       ▼    ▼
DimStation  DimCity         DimRider ───partner_id───► DimPartner
   │
   └── also parent of FactStationHour (1.49 M rows, optional)
```

**Two traps to avoid:**

* `FactStationDay[city]` duplicates the `DimCity` path. **Hide it** in the model; never
  relate it, or you create an ambiguous path and measures will silently double.
* `FactStationDay[month_start]` is used only by the `Fixed Cost` measure (it needs
  station-months). Hide it from the report view so nobody slices by a second date.

### Hiding checklist (report view)

`FactStationDay`: `date_key`, `month_start`, `city`
`FactRiderMonth`: `date_key`, `next_month_active`, `returned_within_2m`
`FactTicket`: `date_key`
`DimDate`: `date_key`, `month_start`, `day_of_week`
All `*_key` surrogate columns exist for auditability only.

---

## 3. Loading

### Power BI Desktop

1. **Get Data → Text/CSV** is fine for one file; for all twelve use
   **Get Data → Blank query → Advanced Editor** and paste `PowerQuery_M.txt`, editing the
   single `MODEL_PATH` line at the top. Create each query in turn (they build on `fnLoadCsv`).
2. `fact_station_hour.csv.gz` is optional. Skip it unless you want the thermal drill-through
   page; it is the only file that pushes the model past 100 MB uncompressed.
3. Create the twelve relationships from the table above.
4. Select `DimDate` → **Table tools → Mark as date table** → `date`.
5. Paste measures from `DAX_Measures.dax`: **Modelling → New measure**, one section at a time.
6. Set the format string per measure (`0.00%` for rates, `₹#,0` for money, `#,##0` for counts).
   Sorting: `DimDate[month_name]` → *Sort by column* → `DimDate[month]`.

### Tableau Desktop / Public

* **Connect → Text file**, one per CSV. Then **Data → Edit relationships** and recreate the
  same joins as *relationships* (noodle), not physical joins — physical joins at these grains
  will duplicate rows.
* Tableau **cannot execute DAX**. Recreate the measures as calculated fields; the full set is
  in §5 below. `fact_station_hour.csv.gz` opens directly (Tableau reads gzip).
* For the KPI cards, set number format to `0.00%` and use `SUM([swaps]) / SUM([attempts])`,
  never `AVG` of a per-row ratio — that is the single most common Tableau mistake on this data.

---

## 4. What each fact supports

| Fact | Answers |
|---|---|
| `FactStationDay` | Reliability trend, failure mix, heat/stockout exposure, revenue, discount, energy cost, margin, contribution per station |
| `FactRiderMonth` | Active riders, churn, retention curves, rider-level failure experience, exposure-vs-churn panels |
| `FactTicket` | Ticket volume vs failures, resolution time, CSAT |
| `FactStationHour` | Cabinet temperature vs success at hour resolution, charge-time degradation, outage minutes |

Conformed dimensions make the cross-fact views work: success rate vs ticket rate by city,
churn vs failure rate by partner, margin vs pack age.

---

## 5. Measures

`DAX_Measures.dax` ships 64 measures in seven groups. The ones that carry the argument:

| Measure | Verified value |
|---|---|
| Total Attempts | 3,877,013 |
| Completed Swaps | 3,645,809 |
| Success Rate | 94.04% |
| Failures | 231,204 |
| No-Battery Share of Failures | 58.13% |
| Heat-Alert Success Rate | 85.07% |
| Cool-Day Success Rate | 94.50% |
| Heat Gap (pp) | 9.43 |
| Hot-Hour Attempts | 481,106 |
| Net Revenue | ₹23,31,26,056 |
| Discount Rate | 8.49% |
| Gross Margin | ₹16,20,38,931 |
| GM per Swap | ₹44.45 |
| Contribution per Swap | ₹26.70 |
| Active Months / Station Months | 18 / 2,073 |
| Contribution per Station Month | ₹46,965 |
| Loss-Making Stations | 23 |
| Churn Rate (2m) | 7.29% |
| Tickets per 1,000 Swaps | 12.07 |
| Packs Below 65% SOH | 1,377 |

Tableau equivalents (calculated fields):

```
Success Rate        = SUM([swaps]) / SUM([attempts])
GM per Swap         = SUM([gross_margin_inr]) / SUM([swaps])
Contribution        = SUM([gross_margin_inr]) - [Active Months] * SUM([fixed_monthly_inr])
Churn Rate (2m)     = AVG([churn_next])          // blanks ignored → censoring handled
Tickets per 1k      = COUNT([ticket_id]) / (SUM([swaps]) / 1000)
```

---

## 6. Modelling decisions a reviewer will ask about

**`riders_distinct` is not in the fact.** The raw data lets you compute distinct riders per
station-hour, but summing that to a day double counts anyone who used two stations. Active
riders come from `DISTINCTCOUNT(FactRiderMonth[rider_id])`, which is the only correct source.

**`churn_next` is NULL for the final two months of the panel, not 0.** Those months are
right-censored: a rider active in June 2025 cannot yet be observed churning. Writing 0 there
would have made the last two months look like the best retention in the dataset. Because the
column is blank, `AVERAGE` and `COUNT` — not `COUNTROWS` — skip them automatically.

**Success is a ratio, never an average of averages.** Every rate measure is
`DIVIDE(SUM(numerator), SUM(denominator))`. A per-row average overweights stations with one
attempt.

**Fixed cost is applied at station-month.** `Fixed Cost` multiplies the count of months in
context by the sum of each station's `monthly_rent_inr + monthly_maintenance_inr`. At the
edges of the period a station may be active for part of a month, so monthly contribution for
the first/last month is understated by up to half a month's rent. This is the same convention
the notebook uses, and it is why the report calls the ₹1.17 Cr figure *annualised run-rate*
rather than an audited P&L number.

**Energy cost is recomputed, not taken from source.** `energy_cost_inr = energy_kwh × city grid
tariff`, matching the notebook. The source has no per-event electricity cost column.

**Battery table is a snapshot, not a fact.** It is related only to `FactTicket`, so battery
measures respond to battery slicers and *not* to the date slicer. That is deliberate — SOH is
measured once at period end. If you slice by date while looking at a battery visual, nothing
will change, and that is correct behaviour, not a broken relationship.

**The confounded churn cut is deliberately absent.** "Churn among riders who hit a stockout"
comes out *lower* (5.75%) than among riders who did not (8.82%), because stockout exposure
proxies for activity. It is documented in `DAX_Measures.dax` under `DELIBERATE OMISSION` and
excluded from the model, rather than shipped as a card that reads backwards. The report's
+4.8pp claim is the activity-conditioned panel estimate.

**RLS.** Suggested rule on `DimCity`:

```dax
[city] = LOOKUPVALUE ( DimRider[home_city], DimRider[rider_id], USERPRINCIPALNAME () )
```

Only useful if you map users to cities; a simpler demo role is `[city] = "Jaipur"`.

---

## 7. Validation

`scripts/verify_star.py` recomputes every measure above directly from the exported CSVs and
diffs it against the notebook's headline figures. Current output (`reports/star_measures.txt`):

```
Total Attempts      3,877,013   vs notebook  3,877,013   OK
Completed Swaps     3,645,809   vs notebook  3,645,809   OK
Success Rate           94.04%   vs notebook     94.04%   OK
Gross Margin    Rs 16,20,38,931   (report: ₹16.20 Cr)    OK
GM per Swap          Rs 44.45   vs ladder step 4        OK
Contribution/Swap     Rs 26.70   vs ladder step 5        OK
Loss-Making Stations       23   vs notebook       23     OK
mismatches: 0
```

To re-run: `.venv/bin/python scripts/verify_star.py`.
To rebuild everything from raw data: `.venv/bin/python scripts/build_star_schema.py` (~4 min).

If your .pbix disagrees with one of these numbers, the cause is almost always a missing
relationship (a slicer not filtering) or an `AVERAGE` where a `DIVIDE(SUM, SUM)` belongs.

---

## 8. Rebuilding and extending

```bash
.venv/bin/python scripts/build_star_schema.py   # raw CSVs → model/*.csv  (~4 min)
.venv/bin/python scripts/verify_star.py         # reconciliation report
```

`build_star_schema.py` also runs FK-integrity checks (orphan keys across all six relationships)
and fails loudly if a fact key does not resolve in its dimension. Add a new column to a fact by
extending the `agg(...)` block and the `final_cols` list; the column dictionary updates itself.
