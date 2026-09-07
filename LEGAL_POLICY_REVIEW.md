# Legal and policy review checklist

Complete this checklist before a repository mutation, external-data request, release, or other public action.

Record the evidence and the reviewer date in the pull request.

This checklist is a project control.

It is not legal advice.

## Scope and stakeholders

- [ ] Describe the exact action and public outputs.
- [ ] Identify publishers, contributors, users, platforms, and people represented in the data.
- [ ] Confirm that the action stays within the approved project scope.

## Rights and website policies

- [ ] Read the dataset license, copyright notice, website terms, and linked policies.
- [ ] Record the basis for each permitted use, including factual extraction and original analysis.
- [ ] Confirm attribution, notice, share-alike, noncommercial, and modification conditions.
- [ ] Confirm that the review does not treat public-record status or an accessible link as a reuse license.
- [ ] Record separate decisions for download, factual extraction, raw redistribution, and derivative visualization in `config.toml`.

## Privacy, confidentiality, and security

- [ ] Confirm that the materials contain no personal, confidential, restricted, or contract-controlled information.
- [ ] Confirm that credentials and local paths cannot enter code, logs, history, artifacts, or fixtures.
- [ ] Confirm source hashes and keep raw downloads outside Git unless the registry approves publication.

## Platforms and dependencies

- [ ] Review repository-hosting and source-platform rules for the planned action.
- [ ] Review dependency licenses, vulnerability findings, and transitive notices.
- [ ] Confirm that only an explicitly approved CI workflow uses network access.

## Release evidence

- [ ] Run tests, static analysis, secret scanning, rights tests, drift detection, and link validation.
- [ ] Scan the complete public history and all public Git references.
- [ ] Inspect releases, Actions artifacts, and LFS objects.
- [ ] Confirm that a clean clone reproduces each committed table and figure.
- [ ] Record unresolved questions and keep affected material excluded.
