# Four pre-cooked cancer-sector study starters

**Source theme review:** October 13, 2026 · **Author:** Paul Skeffington · Prepared with OpenAI

These are **independent, study-aware reference workspaces** aligned thematically
with four publicly described Dartmouth Cancer Center research programs. They
are not Dartmouth-sponsored or endorsed, and contain **no Dartmouth data,
identifiable records, live dataset extracts, analyzed cancer observations,
approved diagnosis models or clinical output**.

The source catalog provides 14 candidate deployment references. **Four have
newly generated pre-cooked research workspace recipes; none automatically
imports data or performs real research analysis.** Other candidates remain
literature-only discovery records.

## Quick use

~~~bash
python -m pip install -e '.[all]'

# See the four immediately scaffoldable reference workflows:
research-template sectors recipes

# Generate your own blank study space from one program:
research-template sectors scaffold \
  --id SGN-02 \
  --out artifacts/studies/gene-expression \
  --title "My tumor expression research question"

# Machine-check its reference integrity, NOT scientific validity:
research-template sectors check-scaffold \
  --root artifacts/studies/gene-expression
~~~

The generator **refuses to overwrite existing directories** and refuses a
symlinked parent directory. It does not connect to an external service or
read a dataset. It produces a reviewer-editable draft protocol and blank
source-column mappings, with the source dictionary/version and access
application URLs provided for manual follow-through.

### What each generated workspace contains

| File | Actual deliverable |
| --- | --- |
| study.json, PROTOCOL.md, README.md | Draft problem, analysis unit, study review checklist and blocked release |
| SECTOR_RECIPE.json | Pinned copy of a public-domain-source-based **recipe**, not actual source data |
| RECIPE_STATE.json | Package SHA-256 binding; data access, model execution, rendering and publication explicitly blocked |
| VARIABLE_MAPPING.csv | Required scientific **roles** and documented source-field hints; **source_column intentionally empty** |
| ANALYSIS_PLAN.md | Study-specific candidate statistical tools, exact preconditions, official documentation and review tasks |
| FIGURE_PLAN.md | Candidate manuscript figures, missing uncertainty conditions and prohibited false interpretations |
| SECURITY_AND_APPROVALS.md | Source access request, authorized storage and manual distribution/review requirements |
| data/, private/, outputs/ | Empty local Git-ignored folders. **Not secure storage or authorization to put restricted records there** |

The package hash proves the recipe matches the installed reference file; it
does not prove institutional data rights, independently validated source
scientific content or publication approval.

## Sector options: one ready-to-scaffold workflow per program

| Recipe | Publicly documented sector | Configured analysis contract | Candidate deliverables |
| --- | --- | --- | --- |
| CPS-02 | Cancer Population Sciences | BRFSS screening and equity, respondent unit, survey weight/PSU/stratum and eligible screening item | Design-aware proportion/CI and eligibility/response-quality figures |
| SGN-02 | Cancer Signaling, Genomes, and Networks | NCBI GEO sample, independent subject, feature/measurement mapping and counts-vs-intensity distinction | Condition-ordered heatmaps, differential-expression volcano plans, multiple-testing checks |
| ICI-02 | Immunology and Cancer Immunotherapy | Single-cell sample/donor/library/cell nesting, assay QC and pseudobulk planning | Per-donor QC and uncertainty-aware composition visualizations |
| TEC-01 | Translational Engineering in Cancer | TCIA collection, approved patient/study/series hierarchy and modality/annotation review | DICOM metadata QC, missingness and annotation coverage; no unreviewed patient split |

These are **pre-cooked plans, not validated ingest adapters**. In particular:
- CPS requires survey-weight and variance-estimation review; simple respondent
  percentages are not population estimates.
- SGN must determine raw RNA-seq count inputs before suggesting DESeq2, or
  appropriate processed-intensity data for limma; no test fits automatically.
- ICI must avoid treating thousands of cells as thousands of independent
  biological replicates.
- TEC requires a patient-level split, verified image permissions and
  reference-standard provenance before building any imaging classifier.

## From starter to your actual research

1. Obtain formal permission for the **specific** source release, documents,
   institution-approved workspace and planned use. Consult
   [data-access security requirements](DATA_ACCESS_AND_SECURITY.md) first.
2. Identify an accession or collection, versioned source dictionary,
   eligibility rules, original variable columns and dataset-specific sample
   hierarchy.
3. Fill the blank **source_column** cells in VARIABLE_MAPPING.csv without
   changing the reference roles. The checker can verify mapping structure,
   **not** correctness of chosen source variables or matching files.
4. Complete the generated study protocol and review gates for estimation,
   confounding, missingness, censoring, nested sampling, weighting, privacy,
   inference and publication.
5. Build a **separate and explicitly reviewed** ingestion/transform adapter
   inside the research project, with local authorization confirmation,
   synthetic adversarial tests, provenance and original-name preservation.
6. Only once input and scientific designs have been independently validated,
   use the generic [R plotting and inference library](../R/README.md)
   and [manuscript delivery guide](MANUSCRIPT_VISUALIZATION_DELIVERY.md)
   to produce held-back internal study figures, followed by figure/privacy/
   data-custodian review before any external publication.

## Official public-source basis

The scientific program grouping comes from the
[Dartmouth Cancer Center research programs directory](https://cancer.dartmouth.edu/scientists-researchers/research-programs)
and its separate [CPS](https://cancer.dartmouth.edu/scientists-researchers/cancer-population-sciences),
[SGN](https://cancer.dartmouth.edu/scientists-researchers/cancer-signaling-genomes-networks),
[ICI](https://cancer.dartmouth.edu/scientists-researchers/immunology-cancer-immunotherapy),
and [TEC](https://cancer.dartmouth.edu/scientists-researchers/translational-engineering-cancer-tec) descriptions.

The underlying source dictionary and rights links belong to the
[CDC BRFSS annual files](https://www.cdc.gov/brfss/annual_data/annual_2023.html),
[NCBI GEO SOFT file specifications](https://www.ncbi.nlm.nih.gov/geo/info/soft.html)
and [GEO access conditions](https://www.ncbi.nlm.nih.gov/geo/info/geo_paccess.html),
and [NCI TCIA collections](https://www.cancerimagingarchive.net/browse-collections/).
The [14-deployable evidence matrix](../references/DARTMOUTH_CANCER_DEPLOYABLE_LITERATURE_MATRIX_2026-10-13.csv)
and [methods literature matrix](../references/DARTMOUTH_CANCER_METHODS_MATRIX_2026-10-13.csv)
provide the expanded roadmap. Researchers must check each linked document's
current source release and use terms rather than assuming broad permission.

## Engineering gates for the next pass

- **S0 — Complete:** Four source-backed, hash-bound, strictly nonexecuting
  workspace recipes; four CLI pathways and synthetic-only negative tests.
- **S1 — Next:** Build source-specific *synthetic* data fixtures and
  strict mock adapters for one exemplar, especially GEO/SGN-02, including
  stable sample matching and count/intensity contract checks.
- **S2:** Prepare independently testable R recipes for statistics and
  uncertainty when the source/design reviews genuinely permit the method.
- **S3:** Reusable manuscript/interactive figure layouts with print QA and
  explicit captions/estimand/unit checks.
- **S4:** Researcher- and institution-authenticated access, disclosure and
  publication approvals, independent of a successful scaffold or test.

A passing check confirms *reference structure only*, never that a dataset was
obtained legally, a transformation or scientific method is valid, a patient
record is protected, or a manuscript is approved.
