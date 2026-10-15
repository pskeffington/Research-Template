# R-first biomedical research: tidyverse and ggplot2

**Author: Paul Skeffington · Prepared with OpenAI**

All R examples follow the [R coding style contract](STYLE_GUIDE.md): source field names preserved, internal snake_case, native `|>`, explicit `dplyr::` and `tidyr::` transformations, and editable layered `ggplot2` figures. R 4.1+ and installed `ggplot2`, `dplyr`, `tidyr`, `tibble` are required. Sourcing these scripts defines functions only, with no downloads, hidden data reads, package installation or file writes.

## Fully runnable tidyverse workflow

~~~r
source("R/research_tidy.R")
source("R/research_plots.R")
source("R/synthetic_demo.R")
source("R/example_tidy_workflow.R")

result <- run_tidy_example(n = 90L, seed = 711L)
print(result$id_audit)
print(result$join_audit)
print(result$site_summary)
print(result$missingness_summary)
print(result$measurements_long)
print(result$figure)
rt_save(result$figure, "artifacts/tidy/relationship.pdf")
~~~

This runnable example demonstrates a source-to-analysis rename, verified one-to-one join, unmatched row audit, reversible wide/long transformation with source units and NA retained, grouped mean/SD/median/IQR/n/missing summaries, and an explicit `ggplot2::ggplot() + geom_point() + scale_color_manual() + labs() + theme` composition.

## Standalone functions and figure calls

~~~r
source("R/research_tidy.R")
source("R/research_plots.R")
source("R/synthetic_demo.R")
participants_clean <- make_synthetic_cohort(n = 90L, seed = 711L)

summary_total <- summarize_measurements(
  participants_clean, "measurement_mg_dl", "mg/dL"
)
summary_by_site <- summarize_measurements(
  participants_clean, "measurement_mg_dl", "mg/dL", by = "site"
)
missingness <- summarize_missingness(
  participants_clean, c("age_years", "measurement_mg_dl")
)

dictionary <- list(
  site = list(label = "Site", unit = "category",
              levels = c("North", "South", "West")),
  age_years = list(label = "Age", unit = "years"),
  measurement_mg_dl = list(label = "Synthetic measurement", unit = "mg/dL")
)
figure_kit <- rt_kit(
  participants_clean, dictionary, study = "Synthetic methods",
  observation_unit = "simulated person",
  source = "make_synthetic_cohort(seed=711)",
  status = "SYNTHETIC / DESCRIPTIVE ONLY"
)
p_hist <- rt_plot(figure_kit, "hist", value = "age_years")
p_box <- rt_plot(figure_kit, "box", value = "measurement_mg_dl", group = "site")
p_violin <- rt_plot(figure_kit, "violin", value = "measurement_mg_dl", group = "site")
p_scatter <- rt_plot(figure_kit, "scatter", x = "age_years", y = "measurement_mg_dl")
p_bar <- rt_plot(figure_kit, "bar", group = "site")
p_corr <- rt_corr_heatmap(participants_clean, c("age_years", "measurement_mg_dl"))
p_heat <- rt_heatmap(
  matrix(c(-1, 0, NA, 1), nrow = 2),
  row_labels = c("G1", "G2"), col_labels = c("S1", "S2"),
  name = "Synthetic deviation", unit = "unitless",
  mode = "diverging", center = 0
)
rt_save(p_box, "artifacts/tidy/boxplot.pdf")
~~~

All return editable `ggplot` objects. The numeric summary interface now returns a **tidy tibble** for both ungrouped and grouped results. Compatibility: `rt_make_synthetic()` aliases `make_synthetic_cohort()`; `rt_summary_by()` now returns a grouped tibble, not its earlier list format. Source `R/research_tidy.R` before `R/research_plots.R`. See the [complete function atlas](../docs/FUNCTION_CALL_SHEET.md) and [figure conventions](../docs/FIGURE_STANDARD.md).

## Explicit permitted-data imports

Only use approved files. For example, after confirming the file exists and units/codes are documented:

~~~r
# participants_source <- readr::read_csv(
#   "data/raw/approved_source.csv",
#   col_types = readr::cols(
#     Subject_ID = readr::col_character(),
#     Age = readr::col_double(),
#     Site = readr::col_character()
#   )
# )
# participants_clean <- rename_source_columns(
#   participants_source, c(participant_id = "Subject_ID",
#                          age_years = "Age", site = "Site")
# )
~~~

The example never reads real records or implies clinical validity.


## Manuscript delivery, interactive exploration, inferential figures, and large heatmaps

For professional figure delivery, source the specific optional modules after `research_tidy.R` and `research_plots.R`. The [manuscript implementation guide](../docs/MANUSCRIPT_VISUALIZATION_DELIVERY.md) provides runnable synthetic examples, review gates and literature provenance.

| Purpose | Function | Module | Requirements |
| --- | --- | --- | --- |
| Vector PDF plus high-resolution PNG + metadata | `rt_manuscript_export()` | `R/manuscript_delivery.R` | ggplot2 |
| Interactive rendering from ggplot | `rt_interactive()` | `R/research_interactive.R` | optional plotly |
| Private/local HTML widget output | `rt_save_interactive()` | `R/research_interactive.R` | optional htmlwidgets |
| Condition-sorted ggplot heatmap | `rt_heatmap_by_condition()` | `R/research_interactive.R` | ggplot2/tidyverse |
| Annotated large gene-expression matrix | `rt_complex_heatmap()` | `R/research_complex_heatmap.R` | optional ComplexHeatmap/circlize |
| PDF/PNG and sample-order provenance for large heatmap | `rt_export_complex_heatmap()` | `R/research_complex_heatmap.R` | ComplexHeatmap |
| Verified effect interval plot | `rt_verified_forest()` | `R/research_inference_plots.R` | externally verified estimates/intervals |
| Verified differential results | `rt_verified_volcano()` | `R/research_inference_plots.R` | externally verified adjusted p-values |

All publication-facing functions require the operator to review input data provenance, sampling units, transformations, typography and privacy. An output file is not inferential or release authorization.


## Adapt the plotting modules to your research

Use the generic `rt_complex_heatmap()` for feature-by-sample matrices when its input contract matches your data. For model-summary matrices, supply an explicitly named model-effect matrix and validate its axes and inferential meaning in **your own study-specific code**; do not label model effects as individual participants.

For any publication-facing graphic, record the analysis unit, original units, transformations, all explicit color-scale decisions, source version and figure review status. Export with `rt_manuscript_export()`, inspect the physical PDF and PNG, and retain the generated metadata alongside the figure.

See [the manuscript-delivery guide](../docs/MANUSCRIPT_VISUALIZATION_DELIVERY.md) for study-neutral examples and [the complete call sheet](../docs/FUNCTION_CALL_SHEET.md) for functions and required inputs.

## Optional caret: grouped classification and test-set reporting

The independently authored [caret methods and literature guide](../docs/CARET_RESEARCH_WORKFLOW.md) documents the primary [Kuhn (2008) software-methods article](https://doi.org/10.18637/jss.v028.i05), CRAN version, train/test leakage controls and class-dependent confusion-matrix interpretation.

With **optional** packages `caret` and `pROC` installed, run the entirely simulated example:

~~~r
source("R/research_caret.R")
results <- run_synthetic_caret_example(seed = 711L)
print(results$fold_audit)
print(results$confusion_matrix$table)
print(results$holdout_metrics)
stopifnot(results$n_shared_subjects == 0L)
~~~

This code splits 80 simulated subjects before using 5-fold, **group-aware** cross-validation for logistic regression. It excludes IDs and visit indices from model predictors, fits median imputation and numeric transforms within training folds, and assesses held-out sensitivity, specificity, PPV, NPV, balanced accuracy, AUROC and Brier score. Results are synthetic and internally validated only; no patient data or external diagnostic claim. An untuned final test set must never be used as a training or resampling set. See `R/tests/test_caret_workflow.R` for positive and negative quality checks.
