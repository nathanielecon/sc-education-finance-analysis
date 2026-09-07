# Data sources

`config.toml` is the authoritative source-rights registry.

The registry is deny by default.

A public source needs a publisher, a landing page, a rights basis, a rights URL, a review date, and explicit publication decisions.

The pipeline rejects an unregistered or unapproved source.

## Approved source

The registry approves the U.S. Bureau of Economic Analysis regional price parity archive for this release.

BEA states that its website information is public domain unless otherwise noted.

BEA requests attribution.

- Data: [Regional price parity archive](https://apps.bea.gov/regional/zip/SARPP.zip)
- Rights: [BEA copyright FAQ](https://www.bea.gov/help/faq/147)
- Review date: 2026-09-07
- Public snapshot: `data/source/bea-rpp-state-2008-2024.csv`
- Published series: all-items state RPP, `LineCode` 1

## Adding a source

Complete `LEGAL_POLICY_REVIEW.md` before any request, repository mutation, or publication that involves a new source.

Add the decision to `config.toml`.

Keep the source excluded unless the review supports both redistribution and derivative visualization.

Add tests for the rights decision, schema, coverage, and release lineage.
