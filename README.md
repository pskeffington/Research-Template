# Research Template — Reproducible Research Starter

**Author: Paul Skeffington · Prepared with OpenAI**

A reusable starter repository for biomedical and general data science, reproducible research, scientific figures, baseline machine learning, and auditable delivery. Everything in the demonstration is **synthetic**. It does not represent patient records, clinical evidence, regulatory qualification, or production-grade diagnostic software.

## Research data access and security — read before importing data

> **Public repository — never upload real participant-level or restricted data.**
> The template contains **synthetic examples only**. Keep patient records,
> controlled genomics, protected DICOM images, sensitive outputs, credentials,
> and licensed files in **institutionally approved storage**, not in GitHub,
> pull requests, Actions artifacts, issues, logs or hosted previews.
> **Having a data dictionary does not grant access to its dataset.**

**Choose the correct access route for each dataset before you download:**

| Data source | Access restriction | Where to apply or read the rules |
| --- | --- | --- |
| **SEER** | Research Data: registration and data-use agreement. Research Plus/NCCR: additional eRA Commons/HHS account requirements; specialized datasets have separate access requests. | [SEER registration and data requests](https://seer.cancer.gov/data/access.html) |
| **NCI GDC / dbGaP** | Public genomic files may be accessible openly; controlled files need the PI's NIH eRA Commons account and project-level dbGaP approval. | [GDC controlled-data application](https://gdc.cancer.gov/access-data/obtaining-access-controlled-data) |
| **NHANES / NCHS** | Published public-use files are available; restricted variables require a formal NCHS Research Data Center proposal and controlled output review. | [NHANES codebooks](https://wwwn.cdc.gov/Nchs/Nhanes/continuousnhanes/default.aspx?BeginYear=2017) · [RDC application](https://www.cdc.gov/rdc/application-process/index.html) |
| **BRFSS / GEO** | Public-release survey or expression data are generally accessible, but obey source-specific use terms, variable restrictions and survey/sample design. | [BRFSS public files](https://www.cdc.gov/brfss/annual_data/annual_2025.html) · [GEO access](https://www.ncbi.nlm.nih.gov/geo/info/geo_paccess.html) |
| **TCIA imaging** | Many public collections; some require registration, a collection-specific license, and permission from TCIA. | [TCIA collection licenses and restrictions](https://wiki.cancerimagingarchive.net/display/Public/Data+Usage+Policies+and+Restrictions) |

**Before working with real data:** (1) identify the exact data release and use
terms; (2) obtain any required PI/institutional, data-use, and IRB/privacy
reviews; (3) wait for recorded access approval; (4) use an approved encrypted
research environment with least-privilege access, MFA as required, and
private audit logs; (5) confirm whether exports, model weights, figures and
manuscripts need disclosure review **before sharing**. Never send restricted
data to external AI services, APIs or third-party clouds without permission.

**[Read the complete data-access application and security guide](docs/DATA_ACCESS_AND_SECURITY.md)** — step-by-step application instructions, data tiers, official links,
NIH's updated controlled-data security requirements, a practical handling
checklist, incident response, and release boundaries. The repository's
Git-ignored directories are **not** an alternative to approved secure
storage. When authorization is uncertain, **use synthetic data only**.

---

## Biomedical AI and RAG literature corpus (October 2026)

The [biomedical AI and retrieval-augmented generation methods guide](docs/BIOMEDICAL_AI_RAG_METHODS.md) and its [27-source machine-readable literature matrix](references/BIOMEDICAL_AI_RAG_LITERATURE_2026-10-14.csv) cover clinical evidence retrieval, agentic medical RAG, computational pathology, single-cell/spatial ML and AI reporting frameworks. These are **scoping references for study design**, not prevalidated code or clinical decision support. Candidate sources and code links remain subject to independent bibliographic, licensing and runtime verification. A regression test guards their provenance/status fields. Restricted health data and externally hosted AI services are governed by the data-access restrictions above.

## Start a new study in five minutes

Read the [first-project walkthrough](docs/QUICKSTART.md) to install the tool, run a synthetic demonstration, and generate a study-neutral workspace with no clinical or private data.

~~~bash
python -m pip install -e '.[all]'
research-template demo --out artifacts/demo --plots --ml
research-template init-study --out artifacts/studies/my-study \
  --title "My Research Question" --objective descriptive \
  --analysis-unit "one observation per sample"
research-template check-study --root artifacts/studies/my-study
~~~

The initializer produces a blank protocol, variable dictionary, source register, and explicitly blocked release state. It refuses to overwrite an existing directory; the structural checker cannot authorize scientific conclusions or publication.
## Publicly documented cancer research sectors

The optional catalog maps the **four Dartmouth Cancer Center research programs** to independent public dataset reference plans. It is an external thematic index, not a Dartmouth-created package, collaboration, affiliation or institutional endorsement. No institutional data, private research records or copyrighted code are included.

```bash
research-template sectors list
research-template sectors list --program SGN
research-template sectors plan --id TEC-01
```

The [program alignment matrix](references/DARTMOUTH_CANCER_PROGRAM_MATRIX_2026-10-13.csv), [14-deployable literature matrix](references/DARTMOUTH_CANCER_DEPLOYABLE_LITERATURE_MATRIX_2026-10-13.csv), and [methods/reporting bibliography](references/DARTMOUTH_CANCER_METHODS_MATRIX_2026-10-13.csv) are preloaded. **All 14 candidates are metadata-only** pending independent schema, licensing, methods, and scientific validation. The already separate NHANES Study Pack remains the only implemented CSV structure-validation pilot.

Read [cancer sector deployment guide](docs/CANCER_RESEARCH_SECTOR_CATALOG.md) for source provenance, design gates, and staged implementation order.

### Pre-cooked workspaces for the four cancer research programs

The optional cancer-sector catalog now contains **four reproducible,
researcher-editable starter recipes** (one per program). These generate a
blank protocol, variable-role mapping, model preconditions and planned
figures; **they do not acquire data, fit a model or release outputs**.

~~~bash
research-template sectors recipes

research-template sectors scaffold \
  --id SGN-02 \
  --out artifacts/studies/my-oncology-study

research-template sectors check-scaffold \
  --root artifacts/studies/my-oncology-study
~~~

| Sector | Starter ID | Initial configuration |
| --- | --- | --- |
| Cancer Population Sciences | CPS-02 | Survey-weighted screening design and uncertainty |
| Cancer Signaling, Genomes, and Networks | SGN-02 | GEO sample/feature alignment and count/intensity inference gates |
| Immunology and Cancer Immunotherapy | ICI-02 | Donor/sample/cell nesting and pseudobulk review |
| Translational Engineering in Cancer | TEC-01 | TCIA patient/study/series hierarchy and imaging QA |

**[Four starter workflows and access requirements](docs/SECTOR_STARTER_RECIPES.md)** —
all references are independent, based on public source documentation, and
**not affiliated with or endorsed by Dartmouth Cancer Center**. The
public README [data access and security notice](docs/DATA_ACCESS_AND_SECURITY.md)
still governs real datasets.

## Study Packs — connect published data dictionaries to your own files

The generic core now supports **opt-in, source-qualified Study Packs**.
The first implementation recognizes three CDC NHANES 2017–2018 files and can
check your local CSVs against their published variables and coding rules
without uploading or modifying their records:

~~~bash
research-template pack list
research-template pack plan --id nhanes-2017-2018
research-template pack validate --id nhanes-2017-2018 \
  --table DEMO_J --csv /approved/local/path/DEMO_J.csv \
  --confirm-authorized-local-use
~~~

**Structural validation is not survey-weighted analysis or publication approval.** Before `pack validate` will open a local CSV, researchers must explicitly acknowledge approved local use with `--confirm-authorized-local-use`; the flag does not confer authorization.
The pack documents SEQN joins, eligibility, units, missing-value codes, and
the need for researcher-reviewed weights, strata and PSU handling. BRFSS,
OMOP and GDC are documented as possible future packs, not working adapters.
Read the [Study Pack guide](docs/STUDY_PACKS.md) for source links, limits
and development gates.

## R/tidyverse coding standard — optional workflow

The R research workflow follows the [whole-repository coding contract](docs/CODING_CONVENTIONS.md), the [R style contract](R/STYLE_GUIDE.md), and the [complete R function sheet](R/README.md). It preserves original source names, uses snake_case analysis fields, explicit native `|>` with `dplyr` and `tidyr`, audited join cardinality, clear missing-value denominators, and layered `ggplot2` grammar.

```r
source("R/research_tidy.R")
source("R/research_plots.R")
source("R/synthetic_demo.R")
source("R/example_tidy_workflow.R")
result <- run_tidy_example()
print(result$join_audit)
print(result$site_summary)
print(result$figure)
```

R 4.1+, `ggplot2`, `dplyr`, `tidyr` and `tibble` are required for this optional R workflow; CI installs them. `readr` is available for explicitly approved CSV imports. There are no downloads or writes when R files are sourced.

## Python quick start (parallel workflow)

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

The run generates synthetic CSV data, numeric and grouped summary-statistics tables (n, missing values, mean, SD, median, quartiles, IQR, range), nine publication-oriented PNG/PDF figure presets with JSON provenance/checksums, baseline ML metrics and a run manifest in `artifacts/demo/` (gitignored). Run without optional packages via `python -m pip install -e .` and `research-template demo`. Audit verifies the scaffold, **not scientific validity**; `research-template audit --require-release` intentionally fails until a specific study passes independent scientific review.

## Find the right tool

| Goal | Start here | Ready-to-call interface |
| --- | --- | --- |
| Coding conventions | **[Whole-repository style contract](docs/CODING_CONVENTIONS.md)** and [R style guide](R/STYLE_GUIDE.md) | GitHub CI enforces both R and Python conventions |
| Configure a study | [Project setup](docs/PROJECT_SETUP.md), [protocol](docs/PROTOCOL.md), [data dictionary](docs/DATA_DICTIONARY.md) | `research-template audit --root .` |
| Find a function | **[Complete biomedical R/Python function sheet](docs/FUNCTION_CALL_SHEET.md)** | `FigureKit`, `kit.summary()`, `kit.box()`, `kit.correlation_heatmap()` |
| Produce scientific figures | [Colors, heatmaps and complete figure conventions](docs/FIGURE_STANDARD.md) | `kit.histogram()`, `kit.missingness()`, `FigureKit.matrix_heatmap()` |
| Start statistical comparison | [Statistical workflow](docs/STATISTICAL_WORKFLOW.md) | R comparison/test recipe with explicit assumptions |
| Develop a prediction model | [ML playbook](docs/ML_PLAYBOOK.md) | `run_classification()`, optional PyTorch |
| Track evidence | [Source register](docs/SOURCE_REGISTER.md), [literature matrix](references/LITERATURE_MATRIX.csv) | `create_manifest()`, `sha256_file()` |
| Release a defensible result | [Release gates](docs/RELEASE_GATES.md) | G0–G5 review and separate deployment permission |
| Use Git / review PRs | [Contributing](CONTRIBUTING.md) | Branch → test → PR → reviewed merge |
| Run R examples | **[Tidyverse R companion](R/README.md)** and [style guide](R/STYLE_GUIDE.md) | `source("R/research_tidy.R")`; `run_tidy_example()` |

## Included capabilities

- **Python core:** zero mandatory runtime dependencies, validated synthetic example, explicit units, missingness and duplicate-key checks, manifest with Git revision, environment versions, SHA-256 outputs.
- **Figures and summaries:** dictionary-driven `FigureKit` declares units and study provenance once, then builds full-axis histograms, boxes, violins, grouped scatters, counts, missingness, Pearson correlation matrices and both heatmap types. Matching R companion, one-call mean/SD/median/IQR/group statistics, category-safe Okabe–Ito colors, Viridis magnitude, centered RdBu diverging heatmaps, missing-gray and 300 dpi PNG/vector PDF + JSON figure trace.
- **Machine learning:** optional scikit-learn group-preserving holdout, training-only imputation/scaling, logistic regression versus dummy baseline, balanced accuracy, AUROC and Brier score. An additional CPU PyTorch example is opt-in.
- **R companion:** R-first tidyverse syntax with `dplyr`, `tidyr`, tibble summaries, native pipes, audited joins and editable `ggplot2` figures. Nothing installs packages or writes files merely when sourced.
- **Governance:** CI, tests, PR checklist, no automatic deployment, data boundary, literature matrix, project protocol and scientific gates.

## Research workflow

`question → literature review → protocol → rights/source register → validate & transform → descriptive analysis → baseline ML (when justified) → figures & statistics → human scientific review → gated release`

Git history and passing CI establish software traceability, not automatically publishable scientific conclusions. Secure clinical datasets, credentials, private model weights, licensed source files and identifiable outputs must **never** be added to this public template. Adapt the data contract to each actual project rather than assuming the synthetic contract applies.

## Make your own project

To create an independent repository from this starter, **Use this template → Create a new repository**.

## Reference architecture

- [Best Practices Git](https://github.com/pskeffington/Best-Practices-Git): research-to-release lifecycle and audit gates.
- [Research literature references](references/LITERATURE_MATRIX.csv): external methods, visualization standards, and reproducibility sources.
- [Literature matrix](references/LITERATURE_MATRIX.csv): authoritative external methodological and tool documentation, with implementation mapping.

**Scope:** reusable template and pedagogical executable examples; not a claim of independent external validation. This template's implementation is original and does not import private datasets or protected teaching materials.


## Manuscript and professional visualization outputs

Use the [R manuscript delivery guide](docs/MANUSCRIPT_VISUALIZATION_DELIVERY.md) and [R function atlas](R/README.md) for condition-ordered annotated ComplexHeatmap figures, confidence-interval forest plots, statistically gated volcano displays, separate Plotly exploratory widgets, and static manuscript PDF/PNG exports. Modules are sourced on demand; public release remains a separate scientific and privacy-review gate.


### Publication and journal delivery

This template is **not tied to any dataset, gene panel, cohort, disease, or journal**. Start with your own question, permitted data, codebook, and research protocol. Configure categorical levels, IDs, statistical units, transforms, effect scales, and source licenses for your specific study.

- [Manuscript and figure delivery](docs/MANUSCRIPT_VISUALIZATION_DELIVERY.md) documents generic PDF/PNG exports, metadata, typography, visual review, supplementary diagnostics, and optional interactive graphics.
- [Journal figure requirements](references/JOURNAL_FIGURE_REQUIREMENTS_MATRIX_2026-10-12.csv) and [reporting frameworks](references/JOURNAL_REPORTING_FRAMEWORKS_2026-10-12.csv) are **dated reference matrices**, not preset requirements or acceptance guarantees. Verify your own target journal's current instructions.
- [R figure modules](R/README.md) cover ggplot2, condition-ordered annotated ComplexHeatmap, forest and volcano plots, and Plotly widgets. These are reusable functions with no required clinical study.
- [Function-call sheet](docs/FUNCTION_CALL_SHEET.md) contains working Python and R calls and preconditions.
- [Research release gates](docs/RELEASE_GATES.md) separate code quality, scientific validity, data rights, and approval to share outputs.

### Use this repository as your own research project

1. Choose **Use this template** on GitHub, or clone the repository.
2. Run the synthetic Python and R examples and baseline tests before substituting your own inputs.
3. Record your study's analysis unit, data dictionary, authorized sources, inclusion/exclusion rules, versioned methods, and assumptions in the project documents.
4. Keep identifiable or licensed data outside a public fork; place outputs in the ignored `artifacts/` directory, and configure explicit validation tests for **your dataset**.
5. Decide whether exploratory plots or hypothesis tests are warranted; report missingness, effect units and uncertainty explicitly. Run human review before any external distribution.

Generic functions are intended to be extended, not to enforce another researcher's study design.

