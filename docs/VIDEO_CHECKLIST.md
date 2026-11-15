# 3-Minute Video — recording checklist

**Status: script written and checked. The video has NOT been recorded.** I cannot record audio
or video, and there is no recording of this project in the workspace. The full script is in
`reports/VIDEO_SCRIPT.md`; this page is the checklist to shoot it.

---

## The four points the brief requires, and where each one lands

| Required point | Script section | Time | Must be said out loud |
|---|---|---|---|
| **Business problem** | 0:00 – 0:25 | 25 s | Growth is not the problem; reliability and margin are. One sentence of scope: 3.88 M attempts, 18 months. |
| **Analytical approach** | 0:25 – 0:55 | 30 s | Cleaning, the failure taxonomy, the binomial model with station fixed effects, the rider-month churn panel, the two DiDs. Name the *methods*, not the libraries. |
| **Key insight** | 0:55 – 2:00 | 65 s | Empty cabinets are a symptom, not a cause — the cause is heat plus one hardware generation. The 1.09 odds ratio is the proof. |
| **Recommendations** | 2:00 – 2:50 | 50 s | Seven initiatives, ₹1.17 Cr/yr, in the corrected order (money first, not heat). |
| Close | 2:50 – 3:00 | 10 s | One-line restatement. Stop talking. |

---

## Before you record

- [ ] 3 minutes is the **hard** limit — read the script aloud once with a stopwatch first. Most
      people run 20% long and then speed up. Cut the competitor sentence if you are over.
- [ ] Have these six numbers on a sticky note: **94.04%**, **85.07%**, **1.09**, **₹58.8 L**,
      **₹26.70**, **₹1.17 Cr**. Everything else is decoration.
- [ ] Screen-share the **dashboard** (`dashboard/VoltRelay_Dashboard.html`) or the executed
      notebook — not slides of bullet points. Showing the real artefact is what separates this
      from a book report.
- [ ] Close Slack, notifications, and personal tabs. Record at 1080p minimum.
- [ ] Say your name and the project name in the first five seconds.

## Shot list — 6 screens

1. **Title / one-line scope** — 3 s.
2. **KPI tab** — success rate trend, the two summer dips visible.
3. **Failure mix** — the 58% no-battery bar.
4. **Odds-ratio chart** — heat holds at ~3× after controls; stock-out at 1.09.
5. **Churn panel** — 2.45% → 39.38% across activity buckets.
6. **Action plan tab** — the seven rows with ₹/year.

---

## Non-negotiable accuracy rules

- [ ] Say **"₹1.17 crore per year"**, not "1.3 crore" — the number changed after the thermal
  prize was re-sized within-station.
- [ ] Do **not** say heat is the biggest lever. It is the biggest *mechanism*; the biggest
  *money* item is the partner discount (₹58.8 L). Cooling is fifth (₹5.8 L).
- [ ] Say **"these are contribution-margin estimates before capex"** once. It is true and it
  pre-empts the obvious challenge.
- [ ] If you mention the pricing pilot, say it **failed its parallel-trends test** in the same
  breath. Do not present a DiD as a clean causal effect when it is not.
- [ ] Do not claim you cleaned data you did not clean, or modelled something you did not model.
  Every claim in the script traces to a cell in the notebook.

---

## The 20 seconds that win or lose it

The single strongest moment in the script is the **self-correction**: you say you first
estimated the thermal prize at ₹19 L, then found that the whole seasonal gap was over-credited,
and corrected it to ₹5.8 L.

Most submissions never revise a number. Doing it on camera, with the reason, is what makes an
evaluator believe the rest of your numbers. Keep it even if you have to cut something else.

## After recording

- [ ] Watch it once at 1.0× with the sound off — is the story readable from the visuals alone?
- [ ] Check the duration is ≤ 3:00 (hard cut, not 3:04).
- [ ] Check the audio is not clipping and no system sound leaked in.
- [ ] Upload unlisted to YouTube or Drive, set link-sharing to **Anyone with the link**, and
      open the link in an incognito window before submitting it.
- [ ] Submit the *link*, not the raw file, unless the brief asks for a file.
