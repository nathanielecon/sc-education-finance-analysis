# Findings and Methodology

## Scope and Data Vintage

The analysis covers Alabama, Arkansas, Florida, Georgia, Kentucky, Louisiana, Mississippi, North Carolina, South Carolina, Tennessee, Virginia, and West Virginia. The matched salary comparison uses FY 2024–25 salary values and 2024 BEA regional price parities. The salary trend adds one NEA estimate for FY 2025–26 and one project-calculated scenario for FY 2026–27. The other current inputs are May 2025 BLS occupational wages and aggregate 2024 NAEP results for public-school students.

## South Carolina Salary Trend

South Carolina's actual average teacher salary increased from $53,329 in FY 2019–20 to $64,050 in FY 2024–25. That was a nominal increase of 20.1%. The FY 2024–25 Southeastern survey estimate was $61,749, so South Carolina's actual was $2,301, or 3.7%, higher.

NEA table E-6 reports a $67,107 estimate for South Carolina in FY 2025–26. The project then adds the enacted $2,000 increase for every cell in the FY 2026–27 state minimum teacher salary schedule. The result is a $69,107 schedule-only scenario.

The scenario is arithmetic, not an official projection. It assumes that the $2,000 schedule change carries through to the statewide average without a change in teacher composition, experience, district supplements, or turnover. The eventual actual may differ.

RFA reports Southeastern average estimates of $63,085 for FY 2025–26 and $65,545 for FY 2026–27. Those figures remain estimates in every table and chart.

## Matched Salary and Purchasing-Power Comparison

The matched state comparison uses FY 2024–25 because it includes South Carolina and all 11 peers in the same RFA survey period. RFA reports South Carolina's $64,050 value as actual and marks every peer value as a revised estimate.

South Carolina ranks third by nominal salary. After adjustment with each state's 2024 all-items RPP, South Carolina's salary is about $68,321 and ranks seventh. Georgia ranks first after adjustment at about $74,318, while Virginia follows at about $73,002.

The adjustment divides nominal salary by RPP divided by 100. It estimates relative purchasing power across states. It is not a take-home-pay calculation and does not model a teacher's household costs.

The later South Carolina estimate and scenario do not enter this ranking. Using them would mix periods and statuses across states.

## Latest-Available Salary Selection

The latest-available table applies a simple priority rule. It selects the latest approved actual for a state, then falls back to that state's latest RFA estimate. South Carolina therefore uses its FY 2024–25 actual, while the 11 peers use FY 2026–27 estimates.

This table shows the newest approved value for each state. It does not support a rank because the observations do not share the same year or status.

## BLS Occupational Wages

The May 2025 OEWS release reports separate statewide wage distributions for occupations. South Carolina's elementary teacher mean was $62,210 and its median was $60,820. The middle school teacher mean was $62,580 and its median was $60,810. The secondary teacher mean was $65,340 and its median was $62,580.

These are statistical estimates for SOC 25-2021, 25-2022, and 25-2031. They cover wage and salary workers in the named occupations across covered employers. They do not measure the same population or definition as RFA's statewide average classroom-teacher salary, and they are not projections for FY 2025–26.

## NAEP Results

The NAEP comparison uses the percentage of public-school students at or above NAEP Proficient. South Carolina's Grade 4 point estimates were 40.0% in mathematics and 32.5% in reading. Its Grade 8 estimates were 23.7% in mathematics and 25.8% in reading.

Within the 12-state group, those point estimates rank fifth, third, fifth, and seventh. The ranks are descriptive. The pipeline does not treat every rank difference as statistically significant.

NAEP Proficient represents competency over challenging subject matter. It is not equivalent to a state's definition of grade-level proficiency.

## South Carolina Regional Prices

South Carolina's 2024 all-items RPP was 93.749. The index was 6.251 points below the national price level. The state's RPP for services other than housing and utilities was 98.284.

## Calculations and Labels

Percentage change uses `(new - old) / old * 100`. Purchasing power uses `nominal / (RPP / 100)`. The pipeline retains full precision until it creates presentation values.

The `status` field distinguishes `actual`, `estimated`, and `modeled_scenario` records. The `is_revised` field preserves RFA's revision marker without changing an estimate into an actual. Each modeled record must identify its method, source inputs, and assumptions.

## Data Lineage

[`observations.csv`](../data/curated/observations.csv) contains the normalized records. [`teacher-salary-peer-comparison.csv`](../data/curated/teacher-salary-peer-comparison.csv) contains the matched nominal and RPP-adjusted salaries. [`latest-available-teacher-salaries.csv`](../data/curated/latest-available-teacher-salaries.csv) contains the unranked priority selection. [`bls-oews-south-carolina-teacher-wages.csv`](../data/curated/bls-oews-south-carolina-teacher-wages.csv) separates BLS means from medians. [`naep-2024-regional-comparison.csv`](../data/curated/naep-2024-regional-comparison.csv) contains all 48 NAEP values and regional point-estimate ranks.

[`source-manifest.json`](../data/source/source-manifest.json) records source URLs, retrieval dates, release labels, content types, source-file hashes for downloads, and snapshot hashes. The NEA and state budget facts were verified manually, so their source documents were not downloaded into the pipeline.

## Sources

- [RFA Teacher Salary Projections](https://www.rfa.sc.gov/resources/education/teacher-salary-projections)
- [RFA FY 2026–27 Survey](https://www.rfa.sc.gov/media/11403)
- [NEA August 2026 Report](https://www.nea.org/sites/default/files/2026-08/2026-rankings-and-estimates-report-august-update.pdf)
- [South Carolina FY 2026–27 Budget](https://www.scstatehouse.gov/sess126_2025-2026/appropriations2026/gab5126.php)
- [SCDE Teacher Salary Schedules](https://ed.sc.gov/finance/financial-data/historical-data/teacher-salary-schedules/)
- [BEA Regional Price Parity Archive](https://apps.bea.gov/regional/zip/SARPP.zip)
- [BLS May 2025 OEWS Tables](https://www.bls.gov/oes/tables.htm)
- [NAEP Data Service](https://www.nationsreportcard.gov/api_documentation.aspx)
