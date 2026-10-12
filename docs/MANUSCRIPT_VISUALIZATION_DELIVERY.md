# Manuscript visualization delivery contract

**Author:** Paul Skeffington · **Prepared with OpenAI**

Literature basis: [the public biomedical visualization evidence matrix](https://github.com/pskeffington/Dartmouth.HSE.Public/blob/main/06_RESOURCES/Literature/BIOSTAT_R_VISUALIZATION_EVIDENCE_MATRIX.md). Core principles: raw data visibility (Weissgerber 2015, 2019), uncertainty and estimation (Ho 2019; Kay 2024), defensible color encodings (Crameri 2020), heatmap annotations (Gu 2016, 2022), and transparent scientific-figure preparation (Jambor 2025). These are methodological references, **not** validation of a specific scientific result.

## Figure review and delivery

1. Preserve supplied variable names and letter case; never silently capitalize input.
2. State analysis unit (participant, specimen, cell), N included/excluded, missingness, transforms, units, group/order and figure legend.
3. Use accessible perceptually meaningful sequential scales for magnitudes, zero-centered diverging scales for signed data. Do not turn row-z scores into absolute gene-expression claims.
4. Violin plots include an internal median/quartile box. Whiskers are not confidence intervals. Keep sample size and independence explicit.
5. For heatmaps, freeze row/sample IDs and normalization orientation. For large matrices, consider ComplexHeatmap with documented clinical sample annotations, grouping by condition, separate annotation legends and missing-value color. Never cluster samples across conditions unless the method and interpretation justify it.
6. Do not generate p values, CIs, adjusted p values, ROC, PR, calibration or volcano significance annotations from descriptive-only effect data. Require an approved inferential result and independently verified model contract.
7. Export vector PDF for manuscript and 600 dpi PNG for previews. Check actual exported images at publication print size, labels, legend clipping, color accessibility, device/font embedding, scaling, and journal specifications. The exporter cannot certify those visually.
8. Private, restricted or PHI-bearing data cannot be approved for public release by the helper. Redact and perform independent human release approval.
9. Interactive Plotly can accompany the paper as a separate exploratory HTML artifact only; redact hover fields and apply deployment content security/privacy review. Never substitute interactive HTML for a vector manuscript panel.

## Runnable example (synthetic)

```r
source("R/research_tidy.R")
source("R/research_plots.R")
source("R/manuscript_delivery.R")
source("R/synthetic_demo.R")
cohort <- make_synthetic_cohort(n = 90L, seed = 711L)
p <- rt_violin(cohort, "site", "measurement_mg_dl",
               y_name = "Synthetic measurement", y_unit = "mg/dL",
               levels = c("North", "South", "West"))
rt_manuscript_export(
  p, "artifacts/manuscript/figure_01", figure_id = "Figure_01",
  legend = "Synthetic participant measurement by site; violin and internal box.",
  study = "Synthetic demonstration", data_status = "SYNTHETIC",
  analysis_unit = "simulated participant", source = "make_synthetic_cohort(seed=711)",
  n_analyzed = nrow(cohort), n_missing = 0L
)
```

The exporter writes a PDF, PNG, RDS sidecar and (when jsonlite is available) JSON sidecar. A PENDING review field remains until a human confirms image appearance, statistical validity and disclosure eligibility. No automatic publication, network traffic or package installation occurs.

## Optional packages

`plotly`/ `htmlwidgets` for an interactive *separate* deliverable; `ComplexHeatmap` and `circlize` for large genomic heatmaps; `ggdist` for uncertainty; `patchwork` for assembled panels; `ragg` for device consistency; `svglite` for editable vectors; `jsonlite` and `digest` for machine-readable sidecars and checksums. Declare exact installed versions in the analysis environment. Do not auto-install these packages.

## Interactive and condition-sorted examples

```r
source("R/research_interactive.R")
mat <- matrix(c(2, 1, 4, 3, 6, 5), nrow = 2)
p <- rt_heatmap_by_condition(
  mat, row_labels = c("Gene A", "Gene B"),
  col_labels = c("Sample A", "Sample B", "Sample C"),
  condition = c("Tumor", "Normal", "Tumor"),
  name = "Synthetic signed deviation", unit = "unitless",
  condition_levels = c("Normal", "Tumor"),
  mode = "diverging", center = 0
)
# Requires approved optional plotly and htmlwidgets packages.
interactive <- rt_interactive(p) # Defaults to no hover text.
rt_save_interactive(interactive, "artifacts/web/synthetic_heatmap.html",
                    data_status = "SYNTHETIC",
                    public_release_approved = FALSE)
```

This helper sorts samples by declared condition order and preserves original sample order within each condition unless `within_condition` is supplied. It does not perform clustering, differential testing or normalization. Plotly tooltip exposure is disabled by default; review hover content separately before any public release. HTML output includes a companion asset directory and is not a journal-ready static figure.

## Forest and volcano plot gates

Source `R/research_inference_plots.R` after the tidy and plots modules. `rt_verified_forest()` requires unique model terms, finite effect estimates, enclosing lower/upper interval bounds, interval level, units, model description, and reference group. Its zero-reference line assumes an additive or log-scale contrast; do not pass raw hazard ratios without an appropriate transformation. `rt_verified_volcano()` requires verified log2 effects and adjusted p values (not descriptive effects), a named contrast, modeling method, and multiple-testing adjustment. It displays adjusted p values of zero at a finite numerical floor.

Neither routine estimates missing inferential quantities. Release requires a separate provenance review of the fitting pipeline, effective sample size, estimand, confidence-interval method, comparison family, and threshold choices. Synthetic tests are at `R/tests/test_inference_plots.R`.


## Large-matrix ComplexHeatmap: grouped conditions and sample annotations

For gene-expression, assay, or biomarker matrices that need multi-track sample annotation and stable condition grouping, use `R/research_complex_heatmap.R`. This is **not a ggplot object**: it returns a ComplexHeatmap bundle rendered separately. Install the optional `ComplexHeatmap` and `circlize` packages in the approved R environment; the CI suite runs a small synthetic rendering test.

```r
source("R/research_tidy.R")
source("R/research_plots.R")
source("R/research_complex_heatmap.R")

# Rows are measured features; columns are precisely labeled samples.
mat <- matrix(c(-1, 2, NA, 4, 3, -3), nrow = 2,
              dimnames = list(c("Gene_A", "Gene_B"), c("T1", "N1", "T2")))
# The metadata rows may arrive in any order; IDs, not row position, govern joins.
samples <- data.frame(
  sample_id = c("T2", "T1", "N1"),
  condition = c("Tumor", "Tumor", "Normal"),
  subtype = c("LumA", "Basal", NA_character_)
)
bundle <- rt_complex_heatmap(
  mat, samples, condition_levels = c("Normal", "Tumor"),
  measurement = "Synthetic signed effect", unit = "log2 units",
  value_transform = "No additional transformation",
  mode = "diverging", center = 0,
  annotations = c("subtype"), rasterize = FALSE
)
stopifnot(identical(bundle$prepared$sample_order, c("N1", "T1", "T2")))
rt_export_complex_heatmap(
  bundle, "artifacts/manuscript/synthetic_heatmap",
  figure_id = "SyntheticHeatmap_01",
  legend = "Synthetic signed values; explicit condition and subtype tracks.",
  source = "Synthetic matrix; no patient records",
  data_status = "SYNTHETIC", width = 9, height = 7, dpi = 600
)
```

**Input/data contract:** Matrix dimensions, nonblank unique sample IDs and feature IDs, one-to-one sample metadata, complete condition labels, a caller-chosen full condition order, and finite numbers or explicit NA cells. Mismatched joins, duplicates, infinite values, undeclared condition levels, and undeclared / excessive annotation categories are rejected. Additional annotation tracks accept categorical values (up to eight categories per track), with missing values represented in gray. Condition levels, sample ordering, missing cells and annotations are recorded in the local provenance sidecar.

**Ordering:** Conditions are kept in the declared order without clustering column slices. Within each condition, the incoming matrix order is preserved, or sort explicitly by a metadata column through `within_condition = "timepoint"`. Rows and columns are *not clustered* by default; a manuscript seeking biological clustering needs a separately documented distance metric, normalization and stability/sensitivity study.

**Normalization:** No row z-scores, batch correction or model fitting are performed by the plotting wrapper. The `value_transform` field must explain upstream transformation; a signed quantity requires an explicit scientifically justified center. Sequential continuous values use a light-to-dark blue palette; signed deviations use blue–neutral–red; missingness is gray. Report row-wise versus global normalization in Methods, not just the caption.

**Scale and export:** The helper hides crowded row labels beyond 65 features and column labels beyond 45 samples unless explicitly overridden. The complete identifier/order metadata is kept in a local RDS sidecar that may itself be sensitive. Default `rasterize = FALSE` preserves vector heatmap cells in the manuscript PDF. Setting it to TRUE can make large exports manageable but **rasterizes the heatmap body** in PDF and must be disclosed. A 600-dpi PNG preview is also emitted. Neither output is automatically reviewed or deployed.

**Release gate:** Review annotation legends, grouping, missingness, all sample identifiers, panel clipping, publication-scale text, palette accessibility, data classification, PDF embedded fonts, output checksums and manuscript legend. If the sidecar contains sample IDs or subtype annotations, treat it with the same privacy controls as the underlying figure. An exported file is not permission to publish.

Primary documentation: [Gu et al. 2016](https://doi.org/10.1093/bioinformatics/btw313); [Gu 2022](https://doi.org/10.1002/imt2.43); [ComplexHeatmap Heatmap API](https://jokergoo.github.io/ComplexHeatmap/reference/Heatmap.html); [ComplexHeatmap split-order behavior](https://jokergoo.github.io/ComplexHeatmap-reference/book/a-single-heatmap.html#order-of-slices).
