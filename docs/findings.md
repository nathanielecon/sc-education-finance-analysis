# Findings and methodology

## Scope

The public release uses BEA regional price parity data through 2024.

It covers South Carolina and 11 peer states named in `config.toml`.

The normalized output includes all five BEA RPP series.

The peer rankings and figures use the all-items series with `LineCode` 1.

An RPP of 100 equals the national price level for that year.

An index below 100 indicates a lower relative price level.

## South Carolina

South Carolina's 2024 RPP was 93.749.

The index was 6.251 points below the national level.

South Carolina ranked fifth-highest among the 12 peer states.

Its RPP increased by 0.518 points between 2014 and 2024.

That change equals 0.56% when the 2014 value is the denominator.

South Carolina's 2024 RPP for services other than housing and utilities was 98.284.

That value comes from `LineCode` 5.

## Peer comparison

Florida recorded the highest 2024 peer value at 103.414.

Virginia followed at 101.104.

Arkansas recorded the lowest peer value at 86.937.

The difference between the highest and lowest peer values was 16.477 points.

These values compare price levels.

They do not measure education spending or educational outcomes.

## Data lineage

The committed source snapshot is [`data/source/bea-rpp-state-2008-2024.csv`](../data/source/bea-rpp-state-2008-2024.csv).

Its acquisition record is [`data/source/source-manifest.json`](../data/source/source-manifest.json).

The normalized output is [`data/curated/observations.csv`](../data/curated/observations.csv).

The 2024 comparison is [`data/curated/south-carolina-peer-comparison.csv`](../data/curated/south-carolina-peer-comparison.csv).

The normalized schema contains `source`, `source_release`, `geography`, `year`, `metric`, `value`, `unit`, and `status`.

All published records have an `actual` status.

The pipeline verifies the source hash before it builds any output.

## Publication boundary

The public build excludes salary, spending, staffing, enrollment, and assessment data.

The exclusion is a conservative publication control.

It is not a conclusion about whether a particular use would be lawful.

See [SOURCE_EXCLUSIONS.md](../SOURCE_EXCLUSIONS.md) for the current decisions.

## Source

- [BEA regional price parity archive](https://apps.bea.gov/regional/zip/SARPP.zip)
- [BEA copyright FAQ](https://www.bea.gov/help/faq/147)
