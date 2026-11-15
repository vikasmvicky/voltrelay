# VoltRelay — submission package

Everything needed for the three deliverables is in this folder. Read this page, then
`docs/COLAB_SETUP.md` (notebook) and `docs/VIDEO_CHECKLIST.md` (video).

---

## What is in here

```
VoltRelay_Submission/
├── START_HERE.md                        ← you are here
├── README.md                            project overview + criteria mapping
├── requirements.txt                     pip install -r requirements.txt
├── notebook/
│   ├── VoltRelay_Analysis.ipynb         ← UPLOAD THIS TO COLAB (97 cells, 17 figures)
│   └── VoltRelay_Analysis_executed.ipynb  same notebook, with verified outputs
├── reports/
│   ├── VoltRelay_Analysis_Report.pdf    ← DELIVERABLE 2 (17 pages, 14 charts)
│   ├── ANALYSIS_REPORT.md               source of the PDF
│   ├── VIDEO_SCRIPT.md                  ← DELIVERABLE 3 script (3:00, not yet recorded)
│   ├── DATA_MANIFEST.csv                8 dataset files + sizes + MD5 + SHA-256
│   ├── key_findings.json                every number, written by the notebook
│   └── star_measures.txt                Power BI measure reconciliation
├── docs/
│   ├── COLAB_SETUP.md                   how to run + publish the Colab notebook
│   ├── VIDEO_CHECKLIST.md               what to say, and what not to overclaim
│   └── POWERBI_STATUS.md                what exists, what does not, how to build the .pbix
├── dashboard/
│   └── VoltRelay_Dashboard.html         8-tab standalone dashboard (no internet needed)
├── figures/                             17 publication PNGs
├── model/                               Power BI star schema: CSVs + 64 DAX measures + guide
└── scripts/                             regeneration and verification scripts
```

---

## Status of the three deliverables

| # | Deliverable | State | Evidence |
|---|---|---|---|
| 1 | **Google Colab notebook** | **Ready to upload.** Executed end-to-end here with 0 errors. Cannot be placed in your Drive by me — the Drive integration is 403-blocked (see below). | 97 cells, 48 code, 17 figures, exit 0, 2m01s |
| 2 | **Analysis report** | **Done as PDF.** 17 pages, 14 charts, tables, methodology, findings, recommendations. | `reports/VoltRelay_Analysis_Report.pdf` |
| 3 | **3-minute video** | **Script only — NOT recorded.** I cannot record video or audio. | `reports/VIDEO_SCRIPT.md` + `docs/VIDEO_CHECKLIST.md` |

---

## Step 1 — Extract

Extract this folder so that it sits at `D:\VoltRelay`:

```
D:\VoltRelay\START_HERE.md
D:\VoltRelay\notebook\VoltRelay_Analysis.ipynb
...
```

## Step 2 — Put the dataset back

The dataset is **847 MB** and is deliberately not inside this ZIP. It is unchanged source data
you already have from the hackathon. Place it so this path exists:

```
D:\VoltRelay\data\Hackathon Data Set | Gradient\swap_events.csv   (728.7 MB)
                                              station_hourly_status.csv  (108.4 MB)
                                              ... all 8 files
```

`reports/DATA_MANIFEST.csv` lists all eight with sizes and checksums, so you can confirm nothing
was truncated. The notebook also runs if the folder sits in your Google Drive instead — that is
the path it uses in Colab.

## Step 3 — Run locally (optional, in VS Code)

```bat
cd D:\VoltRelay
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m ipykernel install --user --name voltrelay --display-name "Python (voltrelay)"
```

Open `notebook\VoltRelay_Analysis.ipynb`, pick the **Python (voltrelay)** kernel, **Run All**.
Expect ~2–3 minutes and 17 figures.

## Step 4 — Upload to Colab and get your link

See `docs/COLAB_SETUP.md`. Short version: put the dataset folder in **My Drive**, upload the
notebook, `Runtime → Run all`, then **Share → Anyone with the link → Viewer**, and verify the
link in an incognito window. The notebook finds the data by itself — no path editing.

---

## What I could not do — plainly

| Blocked | Why | What you must do |
|---|---|---|
| Write the notebook into your Drive | Drive OAuth token has no Drive scopes: `files.get`, `files.list`, `files.create` all return `403 ACCESS_TOKEN_SCOPE_INSUFFICIENT` | Upload `notebook/VoltRelay_Analysis.ipynb` yourself (~1 min) |
| Edit your existing Colab notebook in place | Same 403 | **File → Save a copy in Drive** first (backup), then upload this one |
| Create the shareable link | Creating a file and setting its permissions both need write access | Share → Anyone with the link → Viewer, then check in incognito |
| Record the video | No camera/microphone, and recording your voice is not something I can do | Record from the script; ~30 min including retakes |
| Build a `.pbix` | Power BI Desktop does not run on Linux | Optional. `docs/POWERBI_STATUS.md` has the 20-minute build guide + 64 tested DAX measures |
| Write to `D:\VoltRelay` | This build ran on a remote Linux machine; it cannot see your PC's drives | Extract the ZIP there — that is what it is for |

**No Colab URL is given in this package because none was created.** Any link that appears
anywhere in these files is either your original notebook or an example.

---

## Verification performed

- Notebook re-executed from scratch after the Colab-bootstrap cell was added: **0 errors**,
  48/48 code cells executed, 17 inline figures, 2m01s.
- PDF: 17 pages, 14 figures embedded, text extraction confirms the headline numbers
  (3,877,013 attempts · 94.04% · ₹1.17 Cr · ₹58.8 L · Gen1 · Kyron) are present.
- Power BI model: `scripts/verify_star.py` recomputes 50 measures from the exported CSVs against
  the notebook — **0 mismatches**; all foreign keys resolve (0 orphans).
- Data manifest: all 8 files hashed (MD5 + SHA-256) and sizes match the source folder.
