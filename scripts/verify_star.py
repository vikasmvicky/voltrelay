"""Verify the exported star schema reproduces every number quoted in the report/notebook.

Each block below mirrors one DAX measure from model/DAX_Measures.dax, computed directly
from the exported CSVs. If a .pbix shows something different, the model or the measure is
wrong — this file is the referee.
"""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
M = ROOT / "model"
f = pd.read_csv(M / "fact_station_day.csv", parse_dates=["date"])
rm = pd.read_csv(M / "fact_rider_month.csv", parse_dates=["month_start"])
tk = pd.read_csv(M / "fact_ticket.csv", parse_dates=["created_date"])
bs = pd.read_csv(M / "dim_battery.csv")
st = pd.read_csv(M / "dim_station.csv")

out = []


def m(label, value, fmt="{:,.0f}", expect=None):
    s = fmt.format(value)
    flag = ""
    if expect is not None:
        flag = "  OK" if abs(float(value) - float(expect)) <= max(0.01, abs(expect) * 0.005) else "  MISMATCH"
    out.append(f"{label:38s} {s:>18s}{flag}")
    return value


# --- volume & reliability -------------------------------------------------------------
attempts = m("Total Attempts", f.attempts.sum(), expect=3877013)
swaps = m("Completed Swaps", f.swaps.sum(), expect=3645809)
m("Failures", attempts - swaps, expect=231204)
sr = m("Success Rate", swaps / attempts, "{:.2%}", expect=0.9404)
m("No-Battery Failures", f.fail_no_battery.sum(), expect=134357)
m("Abandoned Queue", f.fail_abandoned.sum(), expect=68400)
m("No-Battery Share of Failures", f.fail_no_battery.sum() / (attempts - swaps), "{:.2%}", expect=0.581)

# --- thermal ---------------------------------------------------------------------------
ha = f.loc[f.heat_alert == 1]
cd = f.loc[f.heat_alert == 0]
ha_sr, cd_sr = ha.swaps.sum() / ha.attempts.sum(), cd.swaps.sum() / cd.attempts.sum()
m("Heat-Alert Success Rate", ha_sr, "{:.2%}", expect=0.8507)
m("Cool-Day Success Rate", cd_sr, "{:.2%}", expect=0.9450)
m("Heat Gap (pp)", (cd_sr - ha_sr) * 100, "{:.2f}", expect=9.43)
hot = f.loc[f.hot_hour_attempts > 0]
m("Hot-Day Success Rate", hot.swaps.sum() / hot.attempts.sum(), "{:.2%}", expect=0.902)
m("Hot-Hour Attempts", f.hot_hour_attempts.sum(), expect=481106)
m("% Attempts in Hot Hours", f.hot_hour_attempts.sum() / attempts, "{:.1%}")
zs = f.loc[f.zero_stock_attempts > 0]
m("Zero-Stock Success Rate", zs.swaps.sum() / zs.attempts.sum(), "{:.2%}")
m("Avg Cabinet Temp (C)", (f.cabinet_temp_avg * f.attempts).sum() / attempts, "{:.1f}")

# --- money -----------------------------------------------------------------------------
rev = m("Net Revenue", f.revenue_inr.sum(), "Rs {:,.0f}")
lst = m("List Value", f.list_inr.sum(), "Rs {:,.0f}")
m("Discount Rate", f.discount_inr.sum() / lst, "{:.2%}")
ec = m("Energy Cost", f.energy_cost_inr.sum(), "Rs {:,.0f}")
gm = m("Gross Margin", f.gross_margin_inr.sum(), "Rs {:,.0f}")
m("Gross Margin %", gm / rev, "{:.2%}")
m("GM per Swap", gm / swaps, "Rs {:,.2f}", expect=44.45)  # notebook ladder step 4
m("kWh per Swap", f.energy_kwh.sum() / swaps, "{:.3f}")
months = f.month_start.nunique()
stm = len(f.groupby(["station_id", "month_start"]))
fixed = months * st.fixed_monthly_inr.sum()
contrib = gm - fixed
m("Active Months", months, expect=18)
m("Station Months", stm)
m("Fixed Cost", fixed, "Rs {:,.0f}")
m("Contribution", contrib, "Rs {:,.0f}")
m("Contribution per Station Month", contrib / stm, "Rs {:,.0f}")
per_station = f.groupby("station_id").gross_margin_inr.sum() - (months * st.set_index("station_id").fixed_monthly_inr)
m("Loss-Making Stations", (per_station < 0).sum(), expect=23)
m("Contribution per Swap", contrib / swaps, "Rs {:,.2f}", expect=26.70)  # ladder step 5
m("Annualised GM Run-Rate", gm / months * 12, "Rs {:,.0f}", expect=1.08e8)

# --- riders & churn --------------------------------------------------------------------
m("Active Riders", rm.rider_id.nunique(), expect=20000)
m("Riders at Risk", rm.churn_next.notna().sum())
churn = m("Churn Rate (2m)", rm.churn_next.mean(), "{:.2%}", expect=0.073)
# The naive stockout cut is confounded by activity (see DAX "DELIBERATE OMISSION").
# It is printed only so the direction of the confound is visible and auditable.
so = rm.loc[rm.stockout > 0].churn_next.mean()
ns = rm.loc[rm.stockout == 0].churn_next.mean()
m("Churn | Stockout Hit (confounded)", so, "{:.2%}")
m("Churn | No Stockout", ns, "{:.2%}")
m("  ^ runs backwards; report uses the panel model, not this", 0, "{:.0f}")
ab = rm.loc[rm.abandoned > 0].churn_next.mean()
m("Churn | Queue Abandoned", ab, "{:.2%}")
m("Rider Failure Rate", 1 - rm.swaps.sum() / rm.attempts.sum(), "{:.2%}")

# --- support & fleet -------------------------------------------------------------------
m("Tickets", len(tk), expect=44000)
m("Tickets per 1,000 Swaps", len(tk) / (swaps / 1000), "{:.2f}")
m("Resolved %", tk.is_resolved.mean(), "{:.1%}")
m("Avg Resolution Hours", tk.resolution_hours.mean(), "{:.1f}")
m("CSAT", tk.csat_score.mean(), "{:.2f}")
m("Packs in Fleet", len(bs), expect=6500)
m("Median Pack SOH", bs.current_soh_pct.median(), "{:.1f}")
m("Packs Below 65% SOH", (bs.current_soh_pct < 65).sum())
m("Retired Packs", bs.is_retired.sum(), expect=1438)

# --- write + report --------------------------------------------------------------------
k = json.loads((ROOT / "reports" / "key_findings.json").read_text())
out.append("")
out.append(f"notebook headline success rate: {k['headline']['success_pct']}%  |  fact: {sr:.2%}")
out.append(f"notebook annual swaps: {k['headline']['swaps']:,}  |  fact: {swaps:,} over {months} months")
txt = "\n".join(out)
(ROOT / "reports" / "star_measures.txt").write_text(txt)
print(txt)
print("\nmismatches:", txt.count("MISMATCH"))
