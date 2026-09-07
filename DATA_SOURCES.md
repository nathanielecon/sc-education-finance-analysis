# Data sources

`config.toml` is the authoritative source registry.

The registry is deny by default.

A public source needs a publisher, a landing page, a review basis, a policy URL, a review date, and explicit use decisions.

The pipeline rejects an unregistered or unapproved source.

## BEA regional price parities

BEA states that its website information is public domain unless otherwise noted. BEA requests attribution.

- Data: [Regional price parity archive](https://apps.bea.gov/regional/zip/SARPP.zip)
- Rights: [BEA copyright FAQ](https://www.bea.gov/help/faq/147)
- Review date: 2026-09-07
- Public snapshot: `data/source/bea-rpp-state-2008-2024.csv`
- Published series: all-items, goods, housing services, utility services, and other services
- Figure series: all-items state RPP, `LineCode` 1

## RFA teacher salary survey

The project uses selected facts from RFA's FY 2026-27 Southeastern Average Teacher Salary Survey. It does not publish the PDF, copy the source table, or reuse RFA's chart or prose.

- Landing page: [Teacher salary projections](https://www.rfa.sc.gov/resources/education/teacher-salary-projections)
- Survey: [FY 2026-27 survey](https://www.rfa.sc.gov/media/11403)
- Policy: [RFA privacy and disclaimers](https://www.rfa.sc.gov/privacy-and-disclaimers)
- Review date: 2026-09-07
- Survey update: 2025-11-19
- Source SHA-256: `0f8a0e37672f8e9b9c7f412b9573134a1bb43975eb231bfec2c4607a5a5feee9`
- Public snapshot: `data/source/rfa-teacher-salary-selected.csv`
- Permitted in this project: download, factual extraction, calculations, and original visualizations
- Excluded from Git: the source PDF and substantial copies of its table, chart, or prose

## Adding a source

Complete `LEGAL_POLICY_REVIEW.md` before any request, repository mutation, or publication that involves a new source.

Add the decision to `config.toml`.

Record separate decisions for download, factual extraction, raw redistribution, and derivative visualization.

Add tests for the rights decision, schema, coverage, and release lineage.
