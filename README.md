# Education

This repository contains the working scripts and spreadsheet automation used to
assemble education finance and compensation datasets from source materials,
clean them for analysis, generate rankings, and prepare reporting outputs.

In plain terms, this is a small workflow repo for turning raw education data
into structured comparison tables and ranked results. It reflects a practical,
tool-mixed process built around Python scripts, Excel/VBA automation, Google
Apps Script extraction, and manual workbook review where needed.

## Workflow

The repository is organized around the main stages of the analysis process:

- `extraction`: pull or scrape source data files.
- `cleaning/transforms`: reshape, combine, standardize, and adjust workbook
  data.
- `rankings`: calculate ranking outputs and comparison views.
- `reporting`: support workbook-based outputs used for review and downstream
  presentation.

## Main Tooling

- Python for data extraction, cleanup, transformations, and ranking logic.
- VBA for Excel workbook automation and repetitive spreadsheet operations.
- Google Apps Script for web/data extraction tasks tied to Google tooling.
- Excel-based workflows for inspection, intermediate review, and final outputs.

## Repository Layout

```text
google-apps-script/   Apps Script extractors and scrapers
python/
  extraction/         Python data collection/parsing scripts
  transforms/         Cleanup, reshaping, adjustment, and combination scripts
  rankings/           Ranking and comparison output scripts
vba/                  Excel automation macros
```

## What This Repository Shows

- End-to-end handling of a data workflow from source extraction through ranked
  outputs.
- Comfort working across multiple automation environments instead of relying on
  a single toolchain.
- Practical spreadsheet-oriented data engineering for real-world reporting
  workflows.

## Notes

- The scripts are primarily set up for a local workflow and currently include
  hard-coded paths in places.
- This repository is best understood as working analysis infrastructure rather
  than a packaged, machine-independent software project.
