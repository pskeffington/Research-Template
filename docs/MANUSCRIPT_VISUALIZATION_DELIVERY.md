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
