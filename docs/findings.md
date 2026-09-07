# Findings and Methodology

## Scope and Data Vintage

The salary series comes from the RFA FY 2026-27 Southeastern Average Teacher Salary Survey, updated November 19, 2025. The survey covers Alabama, Arkansas, Florida, Georgia, Kentucky, Louisiana, Mississippi, North Carolina, Tennessee, Virginia, and West Virginia. It also reports the Southeastern average and South Carolina actual salaries. The price series comes from the BEA state regional price parity release through 2024. A regional price parity of 100 equals the national price level for that year.

## South Carolina and the Regional Average

South Carolina's actual average teacher salary rose from $53,329 in FY 2019-20 to $64,050 in FY 2024-25. That is a nominal increase of 20.1%. The FY 2024-25 Southeastern estimate was $61,749. South Carolina's actual salary was $2,301 above it, a difference of 3.7%.

RFA reports estimated Southeastern averages of $63,085 for FY 2025-26 and $65,545 for FY 2026-27. The later estimate is 3.9% higher than the first. RFA does not report a South Carolina estimate for either year, so the South Carolina line ends with the FY 2024-25 actual value.

## Peer-State Comparison

The state comparison uses FY 2024-25 because RFA reports an actual South Carolina figure for that year. Virginia has the highest nominal salary at $73,808, followed by Georgia at $71,563. South Carolina ranks third at $64,050. Mississippi has the lowest peer estimate at $53,452. RFA marks all 11 peer-state values as revised estimates. The pipeline stores South Carolina as actual and keeps the peers as estimates with `is_revised` set to `true`.

RFA also reports later peer estimates. Virginia has the highest FY 2026-27 estimate at $78,987. Mississippi has the lowest at $56,314.

## Regional Price Adjustment

The adjusted comparison divides each FY 2024-25 salary by its 2024 all-items RPP divided by 100. Georgia ranks first at about $74,318, followed by Virginia at about $73,002. South Carolina's adjusted salary is about $68,321, which ranks seventh of 12 states. Florida ranks last at about $55,480 because its 2024 price level was above the national average.

These adjusted values compare purchasing power across states. They are not forecasts of take-home pay or living expenses for individual teachers.

## South Carolina Regional Prices

South Carolina's 2024 all-items RPP was 93.749. The index was 6.251 points below the national level and ranked fifth-highest among the 12 states in this analysis. The state's all-items RPP increased from 93.231 in 2014 to 93.749 in 2024. Its 2024 RPP for services other than housing and utilities was 98.284.

## Calculations and Labels

Percentage change uses `(new - old) / old * 100`. Purchasing power uses `nominal / (RPP / 100)`. The `status` field distinguishes actual values from estimates. The `is_revised` field records RFA's revision marker without changing an estimate into an actual value. The pipeline rounds only presentation values.

The reported Southeastern average comes directly from the RFA survey. The source does not provide teacher-count weights, so the repository does not calculate a weighted average.

## Data Lineage

The committed source snapshots are [`bea-rpp-state-2008-2024.csv`](../data/source/bea-rpp-state-2008-2024.csv) and [`rfa-teacher-salary-selected.csv`](../data/source/rfa-teacher-salary-selected.csv). The RFA snapshot contains selected facts. [`source-manifest.json`](../data/source/source-manifest.json) records the source URLs, retrieval times, releases, content types, source-file hashes, and snapshot hashes.

[`observations.csv`](../data/curated/observations.csv) contains the normalized records. [`teacher-salary-peer-comparison.csv`](../data/curated/teacher-salary-peer-comparison.csv) contains the nominal and adjusted peer comparisons.

The normalized schema includes `source`, `source_release`, `geography`, `year`, `period`, `metric`, `value`, `unit`, `status`, `is_revised`, and `rpp_year`.

## Sources

- [RFA teacher salary projections](https://www.rfa.sc.gov/resources/education/teacher-salary-projections)
- [RFA FY 2026-27 survey](https://www.rfa.sc.gov/media/11403)
- [RFA privacy statement and disclaimers](https://rfa.sc.gov/page/privacy-statement-disclaimers)
- [BEA regional price parity archive](https://apps.bea.gov/regional/zip/SARPP.zip)
- [BEA copyright FAQ](https://www.bea.gov/help/faq/147)
