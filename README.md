# South Carolina Teacher Salary and Regional Cost Analysis

This project compares South Carolina teacher salaries with the Southeastern average and 11 peer states. It combines selected salary facts from the RFA FY 2026-27 survey with BEA regional price parity data through 2024. The state comparison uses FY 2024-25 salaries so South Carolina appears in both the nominal and price-adjusted rankings. RFA reports South Carolina's figure as actual. RFA marks the peer-state figures as revised estimates.

## Findings

- South Carolina's FY 2024-25 actual average teacher salary was $64,050. The corresponding Southeastern estimate was $61,749.
- South Carolina's actual salary was $2,301, or 3.7%, above that regional estimate.
- South Carolina ranked third of 12 states by nominal salary for FY 2024-25.
- After adjustment with 2024 BEA regional prices, South Carolina ranked seventh at about $68,321.
- The reported Southeastern averages for FY 2025-26 and FY 2026-27 are estimates of $63,085 and $65,545.
- Virginia has the highest FY 2026-27 peer estimate at $78,987. Mississippi has the lowest at $56,314.

## Salary Figures

![Line chart comparing South Carolina actual average teacher salaries with the Southeastern average from FY 2019-20 through FY 2026-27. The regional estimates after FY 2023-24 use a dashed line.](docs/assets/figures/salary-trends.svg)

Source: [S.C. Revenue and Fiscal Affairs Office FY 2026-27 survey](https://www.rfa.sc.gov/media/11403). The dashed segment contains estimates.

![Horizontal bars comparing South Carolina's FY 2024-25 actual average teacher salary with revised estimates for 11 Southeastern peer states. South Carolina ranks third at $64,050.](docs/assets/figures/nominal-salary-comparison.svg)

Source: [S.C. Revenue and Fiscal Affairs Office FY 2026-27 survey](https://www.rfa.sc.gov/media/11403). RFA reports South Carolina's $64,050 figure as actual. RFA marks the 11 peer-state figures as revised estimates.

![Horizontal bars comparing FY 2024-25 teacher salaries after adjustment with each state's 2024 regional price parity. South Carolina ranks seventh at about $68,321.](docs/assets/figures/adjusted-salary-comparison.svg)

Sources: [RFA teacher salary survey](https://www.rfa.sc.gov/media/11403) and [BEA regional price parity archive](https://apps.bea.gov/regional/zip/SARPP.zip). The salary and price data refer to the same comparison period. RFA reports South Carolina's salary as actual. RFA marks the peer-state salaries as revised estimates.

## Regional Price Figures

![Line chart of regional price parity trends for South Carolina and 11 Southeastern peer states from 2014 through 2024.](docs/assets/figures/southeastern-rpp-trends.svg)

![Horizontal bar chart comparing South Carolina's 2024 regional price parity with 11 peer states.](docs/assets/figures/south-carolina-peer-rpp.svg)

## Pipeline

The Python package runs an ETL data pipeline for acquisition, PDF and CSV extraction, schema validation, normalization, analysis, and publication. Each download has a manifest entry with its URL, retrieval time, release, content type, and SHA-256 hash. The pipeline checks source permissions before it downloads or publishes data. It stops when a source layout changes. It also stops for missing values, duplicate state-year rows, incomplete peer coverage, or mismatched snapshot hashes.

![Architecture diagram showing source review, acquisition, validation, normalization, analysis, and publication.](docs/assets/figures/architecture.svg)

## Reproduce the Results

Use Python 3.11 or later. `build` and `check` run offline from the committed factual snapshots.

```bash
git clone https://github.com/nathanielecon/sc-education-finance-analysis.git
cd sc-education-finance-analysis
uv sync --extra dev
uv run sc-education-finance build
uv run sc-education-finance check
```

Standard `pip` installation is also supported.

```bash
python -m venv .venv
python -m pip install -e ".[dev]"
python -m sc_education_finance build
python -m sc_education_finance check
```

The command-line interface has four commands:

- `fetch` downloads approved source files and refreshes their factual snapshots.
- `build` processes the snapshots and creates the tables and figures.
- `refresh` runs `fetch` and `build`.
- `check` rebuilds the outputs and fails if committed results differ.

## Tests and Delivery

pytest covers calculations, state-name normalization, source parsing, revision labels, schema failures, rank ties, hashes, and file adapters. The integration test uses invented PDF, HTML, CSV, and workbook files. GitHub Actions provides test automation and CI/CD. It runs Ruff, mypy, pytest, output drift checks, secret scanning, dependency audits, license reporting, and Markdown link validation. Regular CI stays offline, while a manual workflow performs live source refreshes.

The project uses Python, pandas, Matplotlib, pytest, Ruff, mypy, uv, GitHub Actions, and TikZ.

## Methods and Source Use

The purchasing-power calculation is `nominal salary / (RPP / 100)`. The pipeline keeps full precision for calculations and rounds only chart and table values. The matched comparison uses South Carolina's FY 2024-25 actual salary and the peer states' revised estimates for that year. A separate revision flag preserves the survey's `r` notation. The Southeastern averages shown here are the published survey averages.

The repository excludes the RFA PDF and its table. It stores selected factual salary values. MIT covers the original code and charts. It does not license the RFA publication, BEA names, agency marks, or other third-party material.

See [detailed findings and methodology](docs/findings.md), [data sources](DATA_SOURCES.md), and [third-party notices](THIRD_PARTY_NOTICES.md).
