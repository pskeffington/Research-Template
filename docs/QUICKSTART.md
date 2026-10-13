# First research project: five-minute setup

Research-Template is a study-neutral toolkit. Its example datasets and figures
are synthetic demonstrations, not a prescribed sampling design or validated
clinical result.

## 1. Install and run the synthetic example

Python 3.11+:

~~~bash
git clone https://github.com/pskeffington/Research-Template.git
cd Research-Template
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[all]'
pytest -q
research-template demo --out artifacts/demo --plots --ml
~~~

The demo does not use actual records. R is optional for the Python workflow.
The separate R/tidyverse plotting examples are documented in
[R research modules](../R/README.md).

## 2. Create your own empty study

~~~bash
research-template init-study \
  --out artifacts/studies/my-first-study \
  --title "My Research Question" \
  --objective descriptive \
  --analysis-unit "one sample at one measurement time"

research-template check-study --root artifacts/studies/my-first-study
~~~

Other supported objectives are inferential and predictive. These declare
your intended design, not whether a particular statistical test is appropriate.

Generated files and directories:

| Item | Purpose |
| --- | --- |
| study.json | Study title, objective, analysis unit, explicitly blocked release |
| PROTOCOL.md | Research question, design, statistical plan, review checklist |
| data_dictionary.csv | Empty variable/type/unit dictionary |
| source_register.csv | Empty ownership/license/privacy/source register |
| README.md | Researcher-specific local orientation |
| data/, private/, outputs/ | Git-ignored local folders; NOT protected storage |
| .gitignore | Local exclusions for raw data, outputs and common secrets |

**Only blank metadata and the supplied project title are written.** There is
no data download, ingest, model execution or publication approval.

For a separately version-controlled study, use a folder outside artifacts/;
for temporary development inside this public starter, artifacts/ is gitignored.
Do not place identifiable, restricted or licensed information in Git. Ignore
rules are not encryption or access controls.

The initializer refuses to overwrite an existing directory and preserves
your supplied variable capitalization.

## 3. Supply a project-specific research contract

Complete your protocol, variable dictionary and source register with the
population, analysis unit, estimand, permitted sources, sampling and join
design, uncertainty, missingness, assumptions, transformations, privacy and
legal rights. Review the [project setup guide](PROJECT_SETUP.md).

The checker validates **scaffold structure**, not scientific content.
You must separately create a validated ingestion contract for your own data.

Select appropriate reusable tools:

- [R/tidyverse, ggplot2 and ComplexHeatmap](../R/README.md)
- [Python and R function-call sheet](FUNCTION_CALL_SHEET.md)
- [Manuscript figures and audits](MANUSCRIPT_VISUALIZATION_DELIVERY.md)
- [Statistical comparisons](STATISTICAL_WORKFLOW.md)
- [Optional ML workflows](ML_PLAYBOOK.md)
- [Source governance](SOURCE_REGISTER.md)
- [Publication and release gates](RELEASE_GATES.md)

## 4. Approvals do not come from the scaffold

The new study manifest says DRAFT_UNREVIEWED and BLOCKED by default.
Editing a JSON field cannot authenticate scientific, ethics or data-use
approval. Use separate institutionally appropriate reviewer evidence and
release processes before publishing.

## Troubleshooting

When the command is not on the PATH, activate your environment and run
python -m research_template with the same arguments. PowerShell activation
on Windows is .venv\Scripts\Activate.ps1.

If the output directory exists, choose a different destination. If
check-study reports a missing file, changed header, symlink or approval flag,
restore the intended blank template structure and keep scientific decisions
in independently reviewed documents. The command does not inspect user data.
