# Repository Settings Checklist

These controls require repository-owner or administrator action in the GitHub settings interface. Committing this file does not enable them.

## Discussions

- [ ] Open **Settings → General → Features**.
- [ ] Enable **Discussions**.
- [ ] Create or retain categories for announcements, ideas, questions, and model validation.
- [ ] Update support links after the Discussions URL is active.

## Branch protection for `main`

Open **Settings → Branches** or **Settings → Rules → Rulesets** and create a rule targeting `main`.

Recommended minimum controls:

- [ ] Require a pull request before merging.
- [ ] Require at least one approving review for non-trivial changes.
- [ ] Dismiss stale approvals when new commits are pushed.
- [ ] Require conversation resolution before merging.
- [ ] Require status checks to pass.
- [ ] Require the branch to be up to date before merging where practical.
- [ ] Block force pushes.
- [ ] Block branch deletion.
- [ ] Apply rules to administrators, unless an emergency process is documented.

## Required status checks

Only select checks after they have completed successfully at least once and their exact GitHub check names are visible. Expected checks from the current workflow include the Python matrix jobs and Docker job, but the final names must be copied from an actual workflow run.

- [ ] Require all supported Python-version test jobs.
- [ ] Require the Docker build and health-check job.
- [ ] Confirm that skipped conditional steps do not create unavailable required checks.
- [ ] Revisit required checks whenever job names or the Python matrix changes.

## Actions permissions

Open **Settings → Actions → General**.

- [ ] Allow the actions used by the repository.
- [ ] Keep workflow token permissions at read-only by default.
- [ ] Grant write permissions only to workflows that genuinely require them.
- [ ] Require approval for workflows from untrusted external contributors where appropriate.
- [ ] Review allowed actions and reusable workflows periodically.

## Release automation

- [ ] Confirm the tag-triggered release workflow is enabled.
- [ ] Protect release tags or use a release approval process.
- [ ] Create a GitHub Environment named `release` if deployment approvals are desired.
- [ ] Add required reviewers to the `release` environment.
- [ ] Prefer trusted publishing for PyPI rather than long-lived API tokens.
- [ ] Configure package-index credentials only when publication is approved.
- [ ] Verify tag version equals package version before publishing.
- [ ] Require successful CI before creating a release tag.
- [ ] Retain wheel, source distribution, metadata-validation, and installation evidence.

## Security and maintenance

- [ ] Enable Dependabot alerts and security updates where available.
- [ ] Enable secret scanning and push protection where available.
- [ ] Enable private vulnerability reporting.
- [ ] Review default branch, visibility, merge methods, and deletion of merged branches.
- [ ] Add repository topics for discoverability without overstating validation status.

## Evidence of completion

After changing settings, record:

- date;
- person or role making the change;
- screenshots or exported rule configuration where appropriate;
- exact required-check names;
- release environment and approval policy;
- any deliberate exceptions.

Do not mark a checkbox complete merely because the corresponding workflow or documentation file exists. Settings must be verified in the GitHub interface.