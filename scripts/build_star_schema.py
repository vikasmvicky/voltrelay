"""Export a Power BI / Tableau-ready star schema from the raw VoltRelay CSVs.

Design decisions (documented in model/README_powerbi.md):
  * The 3.88M-row event table is NOT exported as a fact. At that grain a .pbix would be unusable.
    Instead we export two behavioural facts at BI-appropriate grains:
        fact_station_day   (station x date)   ~80k rows
        fact_rider_month   (rider x month)    ~140k rows
    plus fact_ticket (44k) and an optional hourly telemetry fact for thermal drill-through.
  * Every fact carries surrogate-free natural keys to conformed dimensions.
  * Pre-computed money columns (energy cost, gross margin) are materialised so DAX stays simple
    and a Tableau user can drag them straight onto a shelf.
"""
import gzip
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "Hackathon Data Set | Gradient"
OUT = ROOT / "model"
OUT.mkdir(exist_ok=True)

SEP = "\u00b7"


def log(msg):
    print(f"[{SEP}] {msg}")


# ------------------------------------------------------------------ dimensions
log("building dimensions")

stations = pd.read_csv(DATA / "stations.csv", parse_dates=["commissioned_date",
                                                           "decommissioned_date",
                                                           "firmware_updated_date",
                                                           "competitor_within_1_5km_since"])
partners = pd.read_csv(DATA / "fleet_partners.csv", parse_dates=["contract_start_date",
                                                                 "amendment_date"])
riders = pd.read_csv(DATA / "riders.csv", parse_dates=["signup_date"])
batteries = pd.read_csv(DATA / "batteries.csv", parse_dates=["manufacture_date", "commission_date",
                                                             "retired_date"])
context = pd.read_csv(DATA / "city_daily_context.csv", parse_dates=["date"])
tickets = pd.read_csv(DATA / "support_tickets.csv", parse_dates=["created_ts"])
hourly = pd.read_csv(DATA / "station_hourly_status.csv", parse_dates=["hour_start"])

SNAP = pd.Timestamp("2025-06-30")

# ---- dim_date: a real date table, 2023-01-01 .. 2025-07-31 (covers signups + late tickets)
dates = pd.date_range("2023-01-01", "2025-07-31", freq="D")
dim_date = pd.DataFrame({"date": dates})
dim_date["date_key"] = dim_date.date.dt.strftime("%Y%m%d").astype("int32")
dim_date["year"] = dim_date.date.dt.year
dim_date["quarter"] = "Q" + dim_date.date.dt.quarter.astype(str)
dim_date["month"] = dim_date.date.dt.month
dim_date["month_name"] = dim_date.date.dt.strftime("%b")
dim_date["month_start"] = dim_date.date.dt.to_period("M").dt.to_timestamp()
dim_date["year_month"] = dim_date.date.dt.strftime("%Y-%m")
dim_date["week_start"] = dim_date.date.dt.to_period("W").dt.start_time
dim_date["day_of_week"] = dim_date.date.dt.day_of_week + 1
dim_date["day_name"] = dim_date.date.dt.strftime("%a")
dim_date["is_weekend"] = (dim_date.date.dt.day_of_week >= 5).astype("int8")
dim_date["season"] = np.where(dim_date.month.isin([4, 5, 6]), "Summer",
                              np.where(dim_date.month.isin([7, 8, 9]), "Monsoon", "Winter"))
dim_date["is_summer"] = (dim_date.season == "Summer").astype("int8")
dim_date.to_csv(OUT / "dim_date.csv", index=False)

# ---- dim_city
city_tariff = stations.groupby("city").grid_tariff_inr_kwh.mean().rename("avg_grid_tariff_inr_kwh")
dim_city = (stations.groupby("city")
            .agg(stations=("station_id", "nunique"),
                 competitor_stations=("competitor_within_1_5km_since", "count"),
                 slots_2w=("slots_2w", "sum"))
            .join(city_tariff).reset_index())
dim_city["competitor_stations"] = dim_city.competitor_stations.fillna(0).astype(int)
dim_city.to_csv(OUT / "dim_city.csv", index=False)

# ---- dim_station (adds the FIXED COST the contribution measure needs)
st = stations.copy()
st["fixed_monthly_inr"] = st.monthly_rent_inr + st.monthly_maintenance_inr
st["capacity_slots"] = st.slots_2w + st.slots_3w
st["has_competitor"] = st.competitor_within_1_5km_since.notna().astype(int)
st = st.rename(columns={"competitor_within_1_5km_since": "competitor_since",
                        "firmware_version": "station_firmware"})
cols = ["station_id", "city", "zone", "latitude", "longitude", "location_type", "host_type",
        "commissioned_date", "decommissioned_date", "expansion_wave", "charger_generation",
        "slots_2w", "slots_3w", "capacity_slots", "inventory_target_2w", "inventory_target_3w",
        "monthly_rent_inr", "monthly_maintenance_inr", "fixed_monthly_inr",
        "grid_tariff_inr_kwh", "connectivity_tier", "station_firmware", "firmware_updated_date",
        "has_competitor", "competitor_since"]
st[cols].to_csv(OUT / "dim_station.csv", index=False)

# ---- dim_partner
pa = partners.copy()
pa["effective_discount_pct"] = pa.discount_pct_after_amendment.fillna(pa.discount_pct)
pa["n_cities"] = pa.cities_active.str.count(r"\|") + 1
pa[["partner_id", "partner_name", "partner_segment", "vehicle_class", "contract_type",
    "contract_start_date", "discount_pct", "amendment_date", "discount_pct_after_amendment",
    "effective_discount_pct", "peak_surcharge_billable", "payment_terms_days", "cities_active",
    "n_cities"]].to_csv(OUT / "dim_partner.csv", index=False)

# ---- dim_battery (+ deliveries, the degenerate usage counter)
DT = {"battery_out_id": "str"}
sw_lite = pd.read_csv(DATA / "swap_events.csv",
                      usecols=["rider_id", "station_id", "event_ts", "event_type",
                               "queue_wait_sec", "battery_in_id", "battery_out_id",
                               "soh_in_pct", "tariff_code", "list_price_inr", "discount_inr",
                               "amount_charged_inr", "energy_to_recharge_kwh", "sync_mode"],
                      dtype={"rider_id": "category", "station_id": "category",
                             "event_type": "category"})
sw_lite["event_ts"] = pd.to_datetime(sw_lite.event_ts)
sw_lite["completed"] = (sw_lite.event_type == "swap_completed").astype("int8")
for _ev, _c in [("failed_no_charged_battery", "f_no_batt"), ("abandoned_queue", "f_abandon"),
                ("cancelled_by_rider", "f_cancel"), ("failed_system_error", "f_system")]:
    sw_lite[_c] = (sw_lite.event_type == _ev).astype("int8")
deliveries = (sw_lite.loc[sw_lite.completed == 1]
              .groupby(sw_lite.battery_out_id.astype(str)).size().rename("deliveries"))
bt = batteries.copy()
bt["deliveries"] = bt.battery_id.map(deliveries).fillna(0).astype(int)
bt["age_months_snapshot"] = ((SNAP - bt.commission_date).dt.days / 30.4).round(1)
bt["soh_drop_pp"] = (bt.initial_soh_pct - bt.current_soh_pct).round(2)
bt["is_retired"] = bt.retired_date.notna().astype(int)
bt["soh_band"] = pd.cut(bt.current_soh_pct, [0, 65, 70, 75, 80, 85, 90, 101],
                        labels=["<65", "65-70", "70-75", "75-80", "80-85", "85-90", "90+"])
bt[["battery_id", "pack_type", "supplier", "manufacturing_lot", "manufacture_date",
    "commission_date", "rated_capacity_kwh", "purchase_cost_inr", "initial_soh_pct",
    "bms_firmware", "retired_date", "retirement_reason", "current_soh_pct", "soh_band",
    "deliveries", "age_months_snapshot", "soh_drop_pp", "is_retired"]].to_csv(
    OUT / "dim_battery.csv", index=False)

# ---- dim_rider (+ lifetime behaviour and churn flags at three definitions)
rid = riders.copy()
life = sw_lite.groupby("rider_id").agg(first_swap=("event_ts", "min"),
                                       last_swap=("event_ts", "max"),
                                       lifetime_attempts=("completed", "size"),
                                       lifetime_swaps=("completed", "sum"))
rid = rid.merge(life, left_on="rider_id", right_index=True, how="left")
rid["lifetime_failures"] = rid.lifetime_attempts - rid.lifetime_swaps
rid["days_since_last_swap"] = (SNAP - rid.last_swap).dt.days
for d in (30, 60, 90):
    rid[f"churned_{d}d"] = (rid.days_since_last_swap > d).astype("int8")
rid["lifetime_failure_rate"] = (rid.lifetime_failures / rid.lifetime_attempts).round(4)
rid = rid.merge(partners[["partner_id", "partner_name", "partner_segment"]],
                on="partner_id", how="left")
rid["partner_name"] = rid.partner_name.fillna("Independent")
rid["partner_segment"] = rid.partner_segment.fillna("independent")
rid[["rider_id", "partner_id", "partner_name", "partner_segment", "vehicle_class",
     "vehicle_model", "home_city", "home_zone", "signup_date", "signup_channel", "plan_type",
     "declared_shift", "age_band", "kyc_verified", "first_swap", "last_swap",
     "lifetime_attempts", "lifetime_swaps", "lifetime_failures", "lifetime_failure_rate",
     "days_since_last_swap", "churned_30d", "churned_60d", "churned_90d"]].to_csv(
    OUT / "dim_rider.csv", index=False)
del life, rid

# ------------------------------------------------------------------ fact_station_day
log("building fact_station_day")
hourly["swap_hour"] = hourly.hour_start.dt.floor("h")
sw_lite["swap_hour"] = sw_lite.event_ts.dt.floor("h")
sw_lite["date"] = sw_lite.event_ts.dt.normalize()

# station-hour -> station-day (join telemetry first, so temp/stock land on the right day)
sh = (sw_lite.groupby(["station_id", "swap_hour"], observed=True)
      .agg(attempts=("completed", "size"), swaps=("completed", "sum"),
           fail_no_battery=("f_no_batt", "sum"), fail_abandoned=("f_abandon", "sum"),
           fail_cancelled=("f_cancel", "sum"), fail_system=("f_system", "sum"),
           revenue_inr=("amount_charged_inr", "sum"), list_inr=("list_price_inr", "sum"),
           discount_inr=("discount_inr", "sum"), energy_kwh=("energy_to_recharge_kwh", "sum"),
           queue_sum_sec=("queue_wait_sec", "sum"), queue_n=("queue_wait_sec", "size"))
      .reset_index())
sh = sh.merge(hourly[["station_id", "swap_hour", "cabinet_temp_c", "charged_2w_min",
                      "chargers_online"]], on=["station_id", "swap_hour"], how="left")
sh["date"] = sh.swap_hour.dt.normalize()
sh["hot_hour_attempts"] = np.where(sh.cabinet_temp_c > 40, sh.attempts, 0)
sh["zero_stock_attempts"] = np.where(sh.charged_2w_min == 0, sh.attempts, 0)

fsd = (sh.groupby(["station_id", "date"], observed=True)
       .agg(attempts=("attempts", "sum"), swaps=("swaps", "sum"),
            fail_no_battery=("fail_no_battery", "sum"), fail_abandoned=("fail_abandoned", "sum"),
            fail_cancelled=("fail_cancelled", "sum"), fail_system=("fail_system", "sum"),
            revenue_inr=("revenue_inr", "sum"), list_inr=("list_inr", "sum"),
            discount_inr=("discount_inr", "sum"), energy_kwh=("energy_kwh", "sum"),
            hot_hour_attempts=("hot_hour_attempts", "sum"),
            zero_stock_attempts=("zero_stock_attempts", "sum"),
            queue_sum_sec=("queue_sum_sec", "sum"), queue_n=("queue_n", "sum"),
            cabinet_temp_avg=("cabinet_temp_c", "mean"),
            cabinet_temp_max=("cabinet_temp_c", "max"),
            chargers_online_avg=("chargers_online", "mean"))
       .reset_index())
fsd["queue_wait_mean_sec"] = (fsd.queue_sum_sec / fsd.queue_n.replace(0, np.nan)).round(1)
fsd["failures"] = fsd.attempts - fsd.swaps
fsd = fsd.merge(st[["station_id", "city", "grid_tariff_inr_kwh"]], on="station_id", how="left")
fsd["energy_cost_inr"] = (fsd.energy_kwh * fsd.grid_tariff_inr_kwh).round(2)
fsd["gross_margin_inr"] = (fsd.revenue_inr - fsd.energy_cost_inr).round(2)
fsd = fsd.merge(context.rename(columns={"date": "ctx_date"}),
                left_on=["city", "date"], right_on=["city", "ctx_date"], how="left")
fsd["date_key"] = fsd.date.dt.strftime("%Y%m%d").astype("int32")
fsd["month_start"] = fsd.date.dt.to_period("M").dt.to_timestamp()
final_cols = ["date_key", "date", "month_start", "station_id", "city", "attempts", "swaps",
              "failures", "fail_no_battery", "fail_abandoned", "fail_cancelled", "fail_system",
              "revenue_inr", "list_inr", "discount_inr", "energy_kwh", "energy_cost_inr",
              "gross_margin_inr", "hot_hour_attempts", "zero_stock_attempts",
              "queue_wait_mean_sec", "cabinet_temp_avg", "cabinet_temp_max", "chargers_online_avg",
              "heat_alert", "rainfall_mm", "is_public_holiday", "festival_or_event",
              "competitor_promo_active", "ecommerce_sale_event", "grid_outage_hours"]
fsd[final_cols].to_csv(OUT / "fact_station_day.csv", index=False, float_format="%.3f")
del sh

# ------------------------------------------------------------------ fact_rider_month
log("building fact_rider_month")
sw_lite["month_start"] = sw_lite.event_ts.dt.to_period("M").dt.to_timestamp()
frm = (sw_lite.groupby(["rider_id", "month_start"], observed=True)
       .agg(attempts=("completed", "size"), swaps=("completed", "sum"),
            abandoned=("f_abandon", "sum"), stockout=("f_no_batt", "sum"))
       .reset_index())
months = sorted(frm.month_start.unique())
midx = {m: i for i, m in enumerate(months)}
frm["month_idx"] = frm.month_start.map(midx)
active = set(zip(frm.rider_id, frm.month_idx))
frm["next_month_active"] = [(r, m + 1) in active for r, m in zip(frm.rider_id, frm.month_idx)]
frm["returned_within_2m"] = [(r, m + 1) in active or (r, m + 2) in active
                             for r, m in zip(frm.rider_id, frm.month_idx)]
frm["fail_rate"] = (1 - frm.swaps / frm.attempts).round(4)
frm["churn_next"] = np.where(frm.month_idx <= max(midx.values()) - 2,
                             1 - frm.returned_within_2m.astype(int), np.nan)
frm["date_key"] = frm.month_start.dt.strftime("%Y%m%d").astype("int32")
frm[["date_key", "month_start", "rider_id", "attempts", "swaps", "fail_rate", "abandoned",
     "stockout", "next_month_active", "returned_within_2m", "churn_next"]].to_csv(
    OUT / "fact_rider_month.csv", index=False)
del frm, active

# ------------------------------------------------------------------ fact_ticket
log("building fact_ticket")
tk = tickets.copy()
tk["date_key"] = tk.created_ts.dt.strftime("%Y%m%d").astype("int32")
tk["created_date"] = tk.created_ts.dt.normalize()
tk["created_hour"] = tk.created_ts.dt.hour
tk["is_resolved"] = (tk.resolution_status == "resolved").astype("int8")
tk[["ticket_id", "date_key", "created_date", "created_hour", "rider_id", "station_id",
    "battery_id", "channel", "category", "priority", "resolution_status", "is_resolved",
    "resolution_hours", "csat_score"]].to_csv(OUT / "fact_ticket.csv", index=False)

# ------------------------------------------------------------------ fact_station_hour (drill)
log("building fact_station_hour (gzip) — thermal drill-through")
fh = hourly.rename(columns={"hour_start": "hour_start"})
fh["date_key"] = fh.hour_start.dt.strftime("%Y%m%d").astype("int32")
fh["hour"] = fh.hour_start.dt.hour
hourly_swaps = (sw_lite.groupby(["station_id", "swap_hour"], observed=True)
                .agg(attempts=("completed", "size"), swaps=("completed", "sum")).reset_index()
                .rename(columns={"swap_hour": "hour_start"}))
fh = fh.merge(hourly_swaps, on=["station_id", "hour_start"], how="left")
fh[["date_key", "hour_start", "station_id", "hour", "charged_2w_avg", "charged_2w_min",
    "charged_3w_min", "packs_charging", "packs_quarantined", "chargers_online",
    "ambient_temp_c", "cabinet_temp_c", "avg_charge_minutes", "outage_minutes", "grid_kwh",
    "telemetry_status", "attempts", "swaps"]].to_csv(
    OUT / "fact_station_hour.csv.gz", index=False, compression="gzip")

# ------------------------------------------------------------------ column dictionary
DICT = {
    ("fact_station_day", "attempts"): "Swap attempts in the station-day (completed + failed).",
    ("fact_station_day", "swaps"): "Completed swaps.",
    ("fact_station_day", "failures"): "attempts - swaps.",
    ("fact_station_day", "fail_no_battery"): "Failed: no charged battery available.",
    ("fact_station_day", "fail_abandoned"): "Rider gave up while queueing.",
    ("fact_station_day", "fail_cancelled"): "Cancelled by rider.",
    ("fact_station_day", "fail_system"): "Technical/system error.",
    ("fact_station_day", "revenue_inr"): "Amount charged, INR (net of discount).",
    ("fact_station_day", "list_inr"): "List price before discount.",
    ("fact_station_day", "discount_inr"): "Discount given.",
    ("fact_station_day", "energy_kwh"): "Energy drawn to recharge returned packs.",
    ("fact_station_day", "energy_cost_inr"): "energy_kwh x station grid tariff.",
    ("fact_station_day", "gross_margin_inr"): "revenue_inr - energy_cost_inr (before site fixed cost).",
    ("fact_station_day", "hot_hour_attempts"): "Attempts in hours where cabinet temp > 40C.",
    ("fact_station_day", "zero_stock_attempts"): "Attempts in hours with zero charged 2W packs.",
    ("fact_station_day", "cabinet_temp_avg"): "Mean cabinet temperature that day (C).",
    ("fact_station_day", "queue_wait_mean_sec"): "Mean queue wait, weighted by attempts.",
    ("fact_rider_month", "fail_rate"): "1 - swaps/attempts for that rider-month.",
    ("fact_rider_month", "churn_next"): "1 if no swap in either of the next two months; NULL for the final two months (right-censored).",
    ("fact_rider_month", "returned_within_2m"): "True if the rider swapped again within two months.",
    ("dim_station", "fixed_monthly_inr"): "Rent + maintenance per month. Multiply by months in context for contribution.",
    ("dim_battery", "deliveries"): "Lifetime completed deliveries (cycles proxy).",
    ("dim_battery", "soh_drop_pp"): "initial_soh_pct - current_soh_pct.",
    ("dim_rider", "churned_60d"): "Headline churn definition: no swap in the final 60 days.",
    ("dim_partner", "effective_discount_pct"): "Post-amendment discount where one exists.",
}
rows = []
for tbl, file in [("fact_station_day", "fact_station_day.csv"), ("fact_rider_month", "fact_rider_month.csv"),
                  ("fact_ticket", "fact_ticket.csv"), ("dim_date", "dim_date.csv"),
                  ("dim_station", "dim_station.csv"), ("dim_city", "dim_city.csv"),
                  ("dim_rider", "dim_rider.csv"), ("dim_battery", "dim_battery.csv"),
                  ("dim_partner", "dim_partner.csv")]:
    head = pd.read_csv(OUT / file, nrows=5)
    for c in head.columns:
        rows.append({"table": tbl, "column": c, "dtype": str(head[c].dtype),
                     "description": DICT.get((tbl, c), "")})
pd.DataFrame(rows).to_csv(OUT / "_column_dictionary.csv", index=False)

# ------------------------------------------------------------------ integrity + reconciliation
log("reconciling against the notebook's headline numbers")
k = json.loads((ROOT / "reports" / "key_findings.json").read_text())
chk = []
f = pd.read_csv(OUT / "fact_station_day.csv")
chk.append(("attempts", int(f.attempts.sum()), k["headline"]["attempts"]))
chk.append(("swaps", int(f.swaps.sum()), k["headline"]["swaps"]))
chk.append(("revenue_inr", round(float(f.revenue_inr.sum()), 0), round(k["headline"]["revenue"], 0)))
sr = 100 * f.swaps.sum() / f.attempts.sum()
chk.append(("success_pct", round(sr, 2), k["headline"]["success_pct"]))
t = pd.read_csv(OUT / "fact_ticket.csv")
chk.append(("tickets", int(len(t)), len(tickets)))
ok = True
for name, got, want in chk:
    match = abs(float(got) - float(want)) <= max(1.0, abs(float(want)) * 0.0005)
    ok &= match
    print(f"  {name:14s} fact={got:>14,}  notebook={want:>14,}  {'OK' if match else 'MISMATCH'}")

def fk_check(label, child_col, child_df, parent_col, parent_df):
    miss = (~child_df[child_col].dropna().isin(set(parent_df[parent_col].dropna()))).sum()
    print(f"  FK {label:34s} orphans={int(miss)}")
    return miss == 0

ds = pd.read_csv(OUT / "dim_station.csv"); dr = pd.read_csv(OUT / "dim_rider.csv")
db = pd.read_csv(OUT / "dim_battery.csv"); dd = pd.read_csv(OUT / "dim_date.csv")
dp = pd.read_csv(OUT / "dim_partner.csv")
fk_ok = all([
    fk_check("fact_station_day.station_id", "station_id", f, "station_id", ds),
    fk_check("fact_station_day.date_key", "date_key", f, "date_key", dd),
    fk_check("fact_rider_month.rider_id", "rider_id", pd.read_csv(OUT / "fact_rider_month.csv"),
             "rider_id", dr),
    fk_check("fact_ticket.date_key", "date_key", t, "date_key", dd),
    fk_check("dim_station.city", "city", ds, "city", pd.read_csv(OUT / "dim_city.csv")),
    fk_check("dim_rider.partner_id", "partner_id", dr, "partner_id", dp),
    fk_check("fact_ticket.battery_id", "battery_id", t, "battery_id", db),
])

print("\nrow counts:")
for p in sorted(OUT.glob("*")):
    if p.suffix == ".csv":
        n = sum(1 for _ in open(p, encoding="utf-8")) - 1
        print(f"  {p.name:32s} {n:>9,} rows  {p.stat().st_size/1e6:6.1f} MB")
    elif p.suffix == ".gz":
        with gzip.open(p, "rb") as fh:
            n = sum(1 for _ in fh) - 1
        print(f"  {p.name:32s} {n:>9,} rows  {p.stat().st_size/1e6:6.1f} MB")
print("\nreconciliation:", "PASS" if ok else "FAIL", "| FK integrity:", "PASS" if fk_ok else "FAIL")
