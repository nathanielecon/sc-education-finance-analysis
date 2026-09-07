# Legal and Policy Review Checklist

Complete this checklist before a repository mutation, external-data request, release, or other public action.

Record the evidence and the reviewer date in the pull request.

This checklist is a project control.

It is not legal advice.

## Scope and Stakeholders

- [ ] Describe the exact action and public outputs.
- [ ] Identify publishers, contributors, users, platforms, and people represented in the data.
- [ ] Confirm that the action stays within the approved project scope.

## Rights and Website Policies

- [ ] Read the dataset license, copyright notice, website terms, and linked policies.
- [ ] Record the basis for each permitted use, including factual extraction and original analysis.
- [ ] Confirm attribution, notice, share-alike, noncommercial, and modification conditions.
- [ ] Confirm that the review does not treat public-record status or an accessible link as a reuse license.
- [ ] Record separate decisions for download, factual extraction, raw redistribution, and derivative visualization in `config.toml`.

## Privacy, Confidentiality, and Security

- [ ] Confirm that the materials contain no personal, confidential, restricted, or contract-controlled information.
- [ ] Confirm that credentials and local paths cannot enter code, logs, history, artifacts, or fixtures.
- [ ] Confirm source hashes and keep raw downloads outside Git unless the registry approves publication.

## Platforms and Dependencies

- [ ] Review repository-hosting and source-platform rules for the planned action.
- [ ] Review dependency licenses, vulnerability findings, and transitive notices.
- [ ] Confirm that only an explicitly approved CI workflow uses network access.

## Release Evidence

- [ ] Run tests, static analysis, secret scanning, rights tests, drift detection, and link validation.
- [ ] Scan the complete public history and all public Git references.
- [ ] Inspect releases, Actions artifacts, and LFS objects.
- [ ] Confirm that a clean clone reproduces each committed table and figure.
- [ ] Record unresolved questions and keep affected material excluded.

## Release Review: Salary Estimates, BLS, and NAEP

Review date: 2026-09-07

Planned action: publish selected facts, original calculations, original charts, and pipeline code. The release adds one NEA salary estimate, one enacted South Carolina schedule input, six BLS wage estimates, and 48 aggregate NAEP results.

Stakeholders include the source agencies, South Carolina teachers, students represented only in aggregate statistics, repository users, maintainers, and GitHub. The public outputs contain no personal or school-level records.

- [x] BEA states that its published information is public domain unless noted. Attribution is included.
- [x] BLS states that its published material is public domain except identified third-party images. The project uses data only, attributes BLS, and does not use the BLS logo.
- [x] NCES makes the selected aggregate NAEP results available through its public Data Service. The project does not use restricted student- or school-level data.
- [x] RFA use remains limited to selected facts, calculations, and original charts. The source PDF, table, chart, prose, and design remain outside Git.
- [x] NEA use is limited to the attributed `$67,107` fact from table E-6. Automated downloading is disabled. The PDF, table, prose, graphics, and design remain outside Git. This decision is not described as guaranteed fair use.
- [x] The South Carolina budget contributes the enacted `$2,000` schedule change as one attributed fact. The project does not reproduce the budget text or site design.
- [x] The SCDE salary-schedule page is a corroborating link only. The project does not download or copy the schedule.
- [x] GlobalCybers and USAFacts were discovery aids only. Their text, tables, figures, and presentation are not included.
- [x] The NAEP chart states that the values are point estimates, that differences may not be statistically significant, and that NAEP Proficient is not state-defined grade-level proficiency.
- [x] The BLS table separates means from medians and states that OEWS is not an FY 2025–26 projection or a substitute for the RFA statewide average.
- [x] The FY 2026–27 South Carolina value is labeled `modeled_scenario`. Its method, inputs, and assumptions are stored with the record.
- [x] Raw downloads remain ignored unless raw redistribution is approved. Manual NEA and budget source documents are not downloaded by the pipeline.
- [x] Repository changes contain no credentials, private résumé content, personal paths, or confidential information.
- [x] MIT applies only to original code and charts. Third-party data, publications, names, marks, and assets keep their own status.
- [x] GitHub publication remains the repository owner's responsibility. CI uses least-privilege read permissions, and live network requests remain confined to the manual refresh workflow.
- [x] Dependency licenses, vulnerabilities, source hashes, snapshot hashes, tests, drift checks, and local links were checked before publication. GitHub Actions will repeat the checks and run the full-history secret scan before merge.

Unresolved boundary: the selected NEA, RFA, and state-government facts rely on a narrow factual-use decision rather than a broad redistribution license. The repository therefore excludes the underlying publications and any substantial reproduction. This is a conservative project control, not legal advice.
