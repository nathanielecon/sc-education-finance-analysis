# Data Sources

`config.toml` is the authoritative source registry.

The registry is deny by default.

A public source needs a publisher, a landing page, a review basis, a policy URL, a review date, and explicit use decisions.

The pipeline rejects an unregistered or unapproved source.

## BEA Regional Price Parities

BEA states that its website information is public domain unless otherwise noted. BEA requests attribution.

- Data: [Regional price parity archive](https://apps.bea.gov/regional/zip/SARPP.zip)
- Rights: [BEA copyright FAQ](https://www.bea.gov/help/faq/147)
- Review date: 2026-09-07
- Public snapshot: `data/source/bea-rpp-state-2008-2024.csv`
- Published series: all-items, goods, housing services, utility services, and other services
- Figure series: all-items state RPP, `LineCode` 1

## RFA Teacher Salary Survey

The project uses selected facts from RFA's FY 2026-27 Southeastern Average Teacher Salary Survey. It does not publish the PDF, copy the source table, or reuse RFA's chart or prose.

- Landing page: [Teacher salary projections](https://www.rfa.sc.gov/resources/education/teacher-salary-projections)
- Survey: [FY 2026-27 survey](https://www.rfa.sc.gov/media/11403)
- Policy: [RFA privacy statement and disclaimers](https://rfa.sc.gov/page/privacy-statement-disclaimers)
- Review date: 2026-09-07
- Survey update: 2025-11-19
- Source SHA-256: `0f8a0e37672f8e9b9c7f412b9573134a1bb43975eb231bfec2c4607a5a5feee9`
- Public snapshot: `data/source/rfa-teacher-salary-selected.csv`
- Permitted in this project: download, factual extraction, calculations, and original visualizations
- Excluded from Git: the source PDF and substantial copies of its table, chart, or prose

## NEA South Carolina Estimate

The project uses one attributed fact from table E-6 of the August 2026 Rankings and Estimates report: South Carolina's `$67,107` FY 2025–26 estimate. Automated downloading is disabled. The report, table, prose, graphics, and design are not included.

- Landing page: [Educator pay and student spending](https://www.nea.org/resource-library/educator-pay-and-student-spending-how-does-your-state-rank)
- Report: [August 2026 report](https://www.nea.org/sites/default/files/2026-08/2026-rankings-and-estimates-report-august-update.pdf)
- Policy: [NEA terms of use](https://www.nea.org/terms-use)
- Review date: 2026-09-07
- Public snapshot: `data/source/nea-south-carolina-salary-selected.csv`
- Permitted in this project: the single attributed fact, project calculations, and an original trend figure

This is a documented limited-factual-use decision. It is not a guarantee of fair use.

## South Carolina Schedule Increase

The project uses the enacted `$2,000` increase to every cell in the FY 2026–27 State Minimum Teacher Salary Schedule. The budget record supplies the scenario input. The final SCDE schedule page is a corroborating link.

- Budget record: [H. 5126, FY 2026–27](https://www.scstatehouse.gov/sess126_2025-2026/appropriations2026/gab5126.php)
- Final schedules: [SCDE teacher salary schedules](https://ed.sc.gov/finance/financial-data/historical-data/teacher-salary-schedules/)
- Statehouse policy: [Disclaimer](https://www.scstatehouse.gov/studentpage/What/disclaim.shtml)
- SCDE policy: [Privacy and legal notice](https://www.ed.sc.gov/privacy-legal/)
- Review date: 2026-09-07
- Public snapshot: `data/source/sc-teacher-schedule-increase-selected.csv`
- Excluded from Git: budget text, schedule files, and source-page design

## BLS Occupational Wages

BLS states that its published material is public domain, except identified third-party photographs and illustrations. The project queries six May 2025 South Carolina teacher-wage series and cites BLS.

- Data: [May 2025 OEWS tables](https://www.bls.gov/oes/tables.htm)
- API: [BLS Public Data API](https://www.bls.gov/developers/)
- Rights: [BLS copyright information](https://www.bls.gov/opub/copyright-information.htm)
- Review date: 2026-09-07
- Release: May 2025, published May 15, 2026
- Public snapshot: `data/source/bls-oews-south-carolina-teacher-wages-may-2025.csv`
- Published measures: annual mean and annual median wage for SOC 25-2021, 25-2022, and 25-2031

## NAEP Results

The project queries aggregate 2024 results from the official NAEP Data Service. It stores 48 state-measure observations for public-school students. No student-level, school-level, or restricted-use data enter the project.

- Data and API documentation: [NAEP Data Service](https://www.nationsreportcard.gov/api_documentation.aspx)
- Public-data context: [NAEP data available for secondary analysis](https://nces.ed.gov/nationsreportcard/researchcenter/datatools.aspx)
- Rights notice: [U.S. Department of Education copyright status](https://www.ed.gov/about/ed-overview/required-notices/website-policies/copyright-status-notice)
- Review date: 2026-09-07
- Public snapshot: `data/source/naep-2024-southeastern-results.csv`
- Measures: Grade 4 and Grade 8 mathematics and reading, percent at or above NAEP Proficient

The output identifies point-estimate ranks. It does not claim that all differences are statistically significant.

## Adding a Source

Complete `LEGAL_POLICY_REVIEW.md` before any request, repository mutation, or publication that involves a new source.

Add the decision to `config.toml`.

Record separate decisions for download, factual extraction, raw redistribution, and derivative visualization.

Add tests for the rights decision, schema, coverage, and release lineage.
