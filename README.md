# Time Sheet and Check List

A desktop app for intake to generate a per-job "Time Sheet and Check List" PDF, create the job's folder on the network share, log the job, and send the PDF to a printer — replacing the paper form.

## Using the app

Run `dist/TimeSheetChecklist.exe` — no Python install needed. It's a single file; copy it to any intake workstation.

1. Enter the **Job Number** (format `yy-jobnumber`, e.g. `26-25250`). Add an **Ext** (e.g. `4`) if this print is for a job extension like `26-25250-4` — the extension is only shown on the printed form and filename, it doesn't change the job folder.
2. Check the checklists that apply to this job.
3. Optionally add **Custom / Job-Specific Items** — free text, one item per line — for anything unique to this job that isn't in a standard checklist.
4. Pick a **Printer** and click **Generate & Print**.

This creates `J:\<parent>\<job>\` (with `Fieldwork`, `From Client`, and `Research` subfolders) if it doesn't already exist, saves the PDF there, appends an entry to `J:\job_checklist_log.txt`, and sends the PDF to the selected printer.

## Checklist content

Each survey type's checklist lives in `DOCUMENTS/*_chklst.md`: the first line is the checklist's title, and each following line (prefixed with `☐`) is one item. Add or edit these files to change what shows up in the app — no code changes needed. The PDF layout auto-fits whatever checklists (and custom items) are selected onto one page, shrinking font size and adding columns as needed.

## Development

```
python -m venv .venv
.venv\Scripts\pip install reportlab pywin32 pyinstaller
.venv\Scripts\python -m job_checklist.app       # run from source
```

Rebuild the exe after any change to `job_checklist/`:

```
.venv\Scripts\pyinstaller --onefile --windowed --name "TimeSheetChecklist" --add-data "DOCUMENTS;DOCUMENTS" run_app.py
```

The build output goes to `dist/TimeSheetChecklist.exe`.
