# Research Template — Reproducible Biomedical Research Starter

**Author: Paul Skeffington · Prepared with OpenAI**

A reusable, independently written starter repository for biomedical data science, reproducible research, scientific figures, baseline machine learning, and auditable delivery. Everything in the demonstration is **synthetic**. It does not represent patient records, clinical evidence, regulatory qualification, or production-grade diagnostic software.

## Start in five minutes

**Python 3.11+**, Git, and an internet connection for the first dependency installation are required. R is optional.

```bash
git clone https://github.com/pskeffington/Research-Template.git
cd Research-Template
python -m venv .venv
source .venv/bin/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -e '.[all]'
pytest -q
research-template demo --out artifacts/demo --plots --ml
research-template audit --root .
```

The run generates synthetic CSV data, a schema/missingness report, publication-quality PDF/PNG examples, baseline ML metrics and a checksum-indexed manifest in `artifacts/demo/` (gitignored). Run without optional packages via `python -m pip install -e .` and `research-template demo`. Audit verifies the scaffold, **not scientific validity**; `research-template audit --require-release` intentionally fails until a specific study passes independent scientific review.

## Find the right tool

| Goal | Start here | Ready-to-call interface |
| --- | --- | --- |
| Configure a study | [Project setup](docs/PROJECT_SETUP.md), [protocol](docs/PROTOCOL.md), [data dictionary](docs/DATA_DICTIONARY.md) | `research-template audit --root .` |
| Find a function | [Python/R call sheet](docs/FUNCTION_CALL_SHEET.md) | `make_cohort()`, `validate_cohort()`, one-call plots |
| Produce scientific figures | [Figure conventions](docs/FIGURE_STANDARD.md) | `histogram()`, `scatter()`, `group_box()`, `heatmap()`, `save_figure()` |
| Start statistical comparison | [Statistical workflow](docs/STATISTICAL_WORKFLOW.md) | R comparison/test recipe with explicit assumptions |
| Develop a prediction model | [ML playbook](docs/ML_PLAYBOOK.md) | `run_classification()`, optional PyTorch |
| Track evidence | [Source register](docs/SOURCE_REGISTER.md), [literature matrix](references/LITERATURE_MATRIX.csv) | `create_manifest()`, `sha256_file()` |
| Release a defensible result | [Release gates](docs/RELEASE_GATES.md) | G0–G5 review and separate deployment permission |
| Use Git / review PRs | [Contributing](CONTRIBUTING.md) | Branch → test → PR → reviewed merge |
| Run R examples | [R companion](R/README.md) | `source("R/research_plots.R")` |

## Included capabilities

- **Python core:** zero mandatory runtime dependencies, validated synthetic example, explicit units, missingness and duplicate-key checks, manifest with Git revision, environment versions, SHA-256 outputs.
- **Figures:** optional Matplotlib with Okabe–Ito categorical colors, viridis magnitude and diverging palettes; axes, units and denominators are explicit. PNG 300 dpi plus PDF/SVG.
- **Machine learning:** optional scikit-learn group-preserving holdout, training-only imputation/scaling, logistic regression versus dummy baseline, balanced accuracy, AUROC and Brier score. An additional CPU PyTorch example is opt-in.
- **R companion:** optional ggplot2 helpers and an independent synthetic demo; no package installs performed when scripts are sourced.
- **Governance:** CI, tests, PR checklist, no automatic deployment, data boundary, literature matrix, project protocol and scientific gates.

## Research workflow

`question → literature review → protocol → rights/source register → validate & transform → descriptive analysis → baseline ML (when justified) → figures & statistics → human scientific review → gated release`

Git history and passing CI establish software traceability, not automatically publishable scientific conclusions. Secure clinical datasets, credentials, private model weights, licensed source files and identifiable outputs must **never** be added to this public template. Adapt the data contract to each actual project rather than assuming the synthetic contract applies.

## Make your own project

To create an independent repository from this starter, the repository owner must first enable the GitHub **Template repository** setting. Once enabled, use **Use this template → Create a new repository**. Until then, clone it normally. Replace sample study documents, update `pyproject.toml`, adjust schema and CI, and record authorization before reading real data. Do not treat the shared default branch as a staging area.

## Reference architecture

- [Best Practices Git](https://github.com/pskeffington/Best-Practices-Git): research-to-release lifecycle and audit gates.
- [Paul's Notes — public research coding guides](https://github.com/pskeffington/Dartmouth.HSE.Public/tree/main/06_RESOURCES): independent tutorials, visualization interpretation and scientific coding references.
- [Literature matrix](references/LITERATURE_MATRIX.csv): authoritative external methodological and tool documentation, with implementation mapping.

**Scope:** reusable template and pedagogical executable examples; not a claim of independent external validation. This template's implementation is original and does not import private datasets or protected teaching materials.
