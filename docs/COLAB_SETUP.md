# Running this notebook in Google Colab

Everything below is what you do; there is nothing else to configure. The notebook locates its
own data — no paths are hard-coded to this machine or to mine.

---

## Step 1 — Put the dataset in your Drive

Create this folder in **My Drive** (exact name, including the pipe character and spaces):

```
My Drive/
└── Hackathon Data Set | Gradient/
    ├── batteries.csv                 0.6 MB
    ├── city_daily_context.csv        0.2 MB
    ├── fleet_partners.csv            0.0 MB
    ├── riders.csv                    2.1 MB
    ├── station_hourly_status.csv   108.4 MB
    ├── stations.csv                  0.0 MB
    ├── support_tickets.csv           6.5 MB
    └── swap_events.csv             728.7 MB
```

All eight files, 847 MB total. Checksums are in `reports/DATA_MANIFEST.csv` — if a file was
truncated during upload, its `.csv` will open with fewer rows and the notebook will fail late
and confusingly, so verify at least `swap_events.csv`:

```bash
# Windows PowerShell
Get-FileHash "D:\VoltRelay\data\Hackathon Data Set | Gradient\swap_events.csv" -Algorithm MD5
# expected: 829C95F645F0A6B12AC9952DC126B936
```

**Already have the folder in Drive from the hackathon?** No upload needed — skip to Step 3.

### If you would rather not upload 847 MB

The notebook does not need `station_hourly_status.csv` or `swap_events.csv` to *start*; it fails
at the first cell that reads them. Two options:

1. **Use the public source folder.** If your dataset came from a shared Drive folder, paste that
   folder's URL into `COLAB_SHARED_FOLDER_URL` in cell 1 of the notebook. The cell installs
   `gdown` and downloads the folder to `/content/dataset` automatically.
2. **Use Colab's own disk** (session-only, lost on disconnect). Upload the CSVs to `/content/`
   in the same layout; the loader checks `/content/data` and `/content/`.

The notebook already searches, in order:

```
$VOLTRELAY_DATA                         (set by cell 1)
./data/                                 (local checkout)
./                                      (CSVs beside the notebook)
/content/, /content/drive/MyDrive/, /content/drive/MyDrive/datasets/
+ one level down from any of those
```

---

## Step 2 — Decide which notebook you are opening

You have two files. They contain the same code; they differ only in whether outputs are stored.

| File | Use it when |
|---|---|
| `VoltRelay_Analysis.ipynb` | **Upload this to Colab.** Clean inputs — you run it live, so the outputs are genuinely yours. |
| `VoltRelay_Analysis_executed.ipynb` | Read-only archive of the verified run (all 17 figures, all outputs). Good for the report appendix or for a judge who will not run code. |

Both were executed end-to-end and produced **0 errors** (see the Completion Report).

---

## Step 3 — Upload to Colab

### Option A — replace your existing notebook (what you asked for)

Your notebook: `https://colab.research.google.com/drive/1lBbjSVI4j-jeKNf47HR9AUCqpwASBgJa`

1. Open it.
2. **File → Save a copy in Drive** — this is your backup. Confirm the copy exists before you
   continue. (I could not make this backup for you: my Drive access is blocked, see below.)
3. **File → Upload notebook**, choose `VoltRelay_Analysis.ipynb`. Colab creates a *new* tab.
4. **Do not** stop there — the new tab is not yet your original file. To make it replace the
   original: in the new tab use **File → Save a copy in Drive**, then in Drive delete the old
   copy and rename the new one, or simply submit the new tab's link (it is equally valid).

### Option B — new notebook (simplest, no overwrite risk)

1. Colab → **File → Upload notebook** → `VoltRelay_Analysis.ipynb`.
2. Rename it `VoltRelay_Analysis_Final` (**File → Rename**).

Either option ends with a valid Colab notebook in your Drive. Option B cannot damage anything.

---

## Step 4 — Run it

1. **Runtime → Run all** (or `Ctrl+F9`).
2. The first cell mounts your Drive and prints the folder it found. It must say:

   ```
   dataset found: /content/drive/MyDrive/Hackathon Data Set | Gradient
   running in Colab: True
   ```

   If it says `Dataset not found in Drive`, your folder name differs — rename it, or set
   `COLAB_SHARED_FOLDER_URL`, or set `VOLTRELAY_DATA` by hand:

   ```python
   import os; os.environ["VOLTRELAY_DATA"] = "/content/drive/MyDrive/<your folder>"
   ```

3. Runtime is **2–3 minutes** on a standard CPU runtime (measured locally: 2m01s). You will be
   asked once to authorise Drive access — allow it.
4. Expected result: 48 code cells, 17 inline figures, no red tracebacks. The last cells write
   `figures/*.png` and `reports/key_findings.json` into the Colab working directory.

**Memory:** Colab's free tier gives ~12.7 GB. The notebook was written to survive on **3 GB**
(that is what this build machine had, and the OOM-kill fix is documented in §11 of the
notebook), so memory is not a constraint in Colab.

---

## Step 5 — Publish and share

1. **Share** (top right) → **General access** → **Anyone with the link** → role **Viewer**.
2. Copy the link. It should look like:
   `https://colab.research.google.com/drive/<FILE_ID>?usp=sharing`
3. **Verify it in a private/incognito window** — signed out. If the notebook opens and shows
   outputs, the link works for your evaluators. This is the only test that counts.
4. If you want the **executed** outputs visible to a viewer who will not run it: after Run All,
   **File → Save** (`Ctrl+S`). Colab keeps outputs in the saved file.

> A Colab link is only valid while the file exists in your Drive. Trashing the file breaks the
> link silently.

---

## What I could not do, and why

| Task | Status | Reason |
|---|---|---|
| Edit your existing notebook directly | **Blocked** | The Drive integration's OAuth token lacks Drive scopes. `files.get`, `files.list` and `files.create` all return `403 insufficientPermissions` / `ACCESS_TOKEN_SCOPE_INSUFFICIENT`. |
| Create a new notebook in your Drive | **Blocked** | Same 403 on create. No file was created; no link exists to give you. |
| Set "Anyone with the link" | **Blocked** | Requires write access to the file's permissions. |
| Execute the notebook inside your Colab account | **Not possible** | Needs an authenticated Google session in a browser I cannot sign into. |
| Execute the notebook here | **Done** | `nbconvert` against the real dataset: exit 0, 2m01s, 0 errors, 17 figures. |

The re-authorisation that would fix this is on the Freebuff side (the Drive app's consent
scopes), not something you can change from a Colab setting. Uploading two files by hand takes
about a minute and needs no permissions beyond your own Drive account.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `403 insufficientPermissions` in a Drive cell | Drive not mounted / consent denied | Re-run cell 1 and allow access; check for the Google authorisation popup being blocked. |
| `FileNotFoundError: swap_events.csv` | Folder name or nesting differs | The cell prints every path it tried — copy the correct path into `VOLTRELAY_DATA`. |
| Kernel dies during Q5 | Out of memory on a tiny runtime | Runtime → Change runtime type → **High-RAM**; the notebook needs ~2.5 GB peak. |
| Figures not showing | `%matplotlib inline` cell skipped | Run all from the top; do not start mid-notebook. |
| `ModuleNotFoundError: scipy` | Rare, trimmed runtime | `!pip install scipy` in a cell, then re-run. |
| Notebook is read-only | Opened via a link with Viewer role | **File → Save a copy in Drive** to get your own editable copy. |
