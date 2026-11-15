# 3-Minute Video Script

**Target length:** 2:50–3:00 · **Delivery:** ~150 words/minute · **Audience:** VoltRelay operations and customer-experience leadership
**Order (as required):** business problem → analytical approach → key insight → recommendations

Read the bold lines as your beats. Timings are cumulative.

---

### 0:00 – 0:25 · The business problem

> **VoltRelay runs 152 battery-swap stations across six Indian cities for delivery riders. In eighteen months it grew swaps by 191% — and on the surface, nothing is wrong: 94% of attempts succeed.**
>
> **But leadership asked three questions: is the network really performing, what is actually causing failed swaps, churn and margin loss, and what should we fix first. I analysed 3.88 million swap attempts, 1.49 million station-hours of telemetry, 6,500 batteries, 44,000 support tickets and 20,000 riders to answer that.**

### 0:25 – 0:55 · The analytical approach

> **I worked in four layers. First, a KPI baseline — because an 18-month average hides everything. Second, I tested each candidate driver on its own: battery stock, cabinet temperature, charger hardware, battery health, weather, connectivity.**
>
> **Third — and this is the important step — every one of those drivers is correlated with the others: hot days are also busy days, and the oldest cabinets sit in the oldest cities. So I fitted a binomial model over all 3.88 million attempts to hold everything constant and separate primary drivers from secondary contributors.**
>
> **Fourth, I used two natural experiments — a peak-pricing rollout and a competitor opening — as difference-in-differences tests, and I checked the assumptions instead of assuming them.**

### 0:55 – 2:00 · The insight

> **Here is what the data says. Success rate is 95.7% for eleven of eighteen months. It only breaks in summer: 90% in 2024, 92% in 2025.**
>
> **That is not growth eroding quality. It is heat. On heat-alert days success falls to 85%. Cabinet temperature above 40 degrees triples the odds of a failed swap — odds ratio 3.1 to 3.3.**
>
> **Now the counter-intuitive part. The obvious culprit is empty cabinets — riders arriving to find no charged battery. Marginally that looks huge: 88% success when a cabinet is empty versus 95% when it is full. But once I control for heat, hour and station, empty stock is worth only an odds ratio of 1.09. It is a symptom of hot, busy hours — not the cause. And adding stock to the model does not change the heat effect at all, so heat is failing riders even when packs are on the shelf.**
>
> **Second insight: the failure is concentrated in an addressable cohort. All ten worst stations are Gen1 cabinets in Jaipur and Delhi, and they drop to 79–88% every April to June while the rest of the network holds 95.5%.**
>
> **Third: one battery supplier, Kyron, loses 9.5 state-of-health points per hundred deliveries versus 2.9 for the others. A quarter of the fleet. And all 1,438 packs were written off on a single day in June 2025 — removing 21% of active packs just as demand peaked.**
>
> **On churn, the obvious test is misleading: riders with zero failed swaps churn most, at 51%. That is activity level, not reliability. Once I condition on being active, churn rises monotonically with failure rate — 2.5% to 39%. Real, but a five-point effect, not the main driver.**
>
> **And margin? Not pricing. Twenty-three under-used new stations lose 2.4 lakh rupees a month, and one partner contract amended from 12% to 28% leaks another 4.9 lakh a month.**
>
> **One thing I had to correct in my own work: my first estimate blamed the whole summer gap on heat, which over-credited it. Once I compared hot hours to cool hours at the same cabinet, the thermal prize is 5.8 lakh a year — not 19. The mechanism is right; the size was wrong. That correction is why the recommendations below are ordered the way they are.**

### 2:00 – 2:50 · The recommendations

> **So, in priority order — and note that money, not heat, comes first.**
>
> **One: cap that 28% partner discount. 59 lakh rupees a year, the largest single number on this list, and it needs no capex.**
>
> **Two: fix or exit the 23 loss-making stations — 28 lakh a year.**
>
> **Three: replace the Gen1 cabinets in Jaipur and Delhi — 13 lakh a year, and it is the biggest reliability lever we have.**
>
> **Four: a virtual queue with a pack hold, to convert the 68,000 riders who abandon a queue every eighteen months — 10 lakh.**
>
> **Five: cool the twelve worst cabinets — 5.8 lakh. Six: keep a minimum charged-pack floor in peak hours.**
>
> **Seven: re-bid the Kyron contract and put a degradation warranty in it. That one is a supply-risk play, not a margin play — a quarter of the fleet degraded three times faster than the rest and disappeared in a single day.**
>
> **Together that is about 1.17 crore rupees of gross margin a year. But the sequencing matters more than the total: items one and two pay for themselves, and item three has to be done before next April.**

### 2:50 – 3:00 · Close

> **The network does not have a growth problem or a software problem. It has a thermal-capacity problem sitting on one hardware generation and one supplier — and an under-used cost base on top of it. Fix those, and 95.7% becomes the number leadership sees all year. Thank you.**

---

## Production notes

- **Slides (6, one per beat):** (1) the three questions + dataset sizes; (2) the four-layer approach with the "everything is correlated" point; (3) the summer-collapse chart and the odds-ratio table; (4) the Gen1 summer chart + Kyron degradation chart; (5) the recommendation table with rupees.
- **Charts to show, in this order:** `01_q1_kpi_trend.png` → `06_q2_odds_ratios.png` → `04_q2_thermal.png` → `05_q2_battery_supplier.png` → `10_q3_panel_churn.png` → `16_q11_cooling_targets.png` → `17_q10_priorities.png`.
- **If you run short:** cut the competitor sentence and the margin detail. Never cut the "stock is a symptom" line, and never cut the self-correction — an analyst who revises a number down is more credible than one who does not.
- **If you run long:** drop the margin detail to one sentence ("23 sites and one contract").
- **Say the numbers slowly.** 95.7%, 85%, 3.1×, 1.09, 9.5 versus 2.9, 58.8 lakh, 1.17 crore. Those carry the argument.
- **One honest caveat, said once:** "this is observational data — I can show well-controlled association, not proof of causation; the cooling pilot is the test."
