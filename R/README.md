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


## Research-aligned PAM50 heatmap figures

Load `R/research_pam50_heatmaps.R` after `R/research_tidy.R` and `R/research_plots.R`. The explicit calls are `rt_pam50_profile()`, `rt_prepare_pam50_research(signature, contrasts)`, `rt_pam50_research_heatmaps(signature, contrasts)`, and `rt_export_pam50_research(bundle, output_dir, source)`.

Unlike a typical sample-by-feature heatmap, **PAM50 subtype columns here are modeled paired effects**, not biological samples. The adapter follows the research project's R11/R19 ST09/ST07 frozen contract: 60 gene rows (15 per anchor), four subtype effects and six contrasts, with case-preserving names, Ensembl fallback labels and one-to-one gene/contrast reconciliation. Shared zero-centered color scales and patient-pair denominators are documented; no new FDR, confidence interval, sample selection, model training or publication approval is implied. Read the [full input and output workflow](../docs/MANUSCRIPT_VISUALIZATION_DELIVERY.md#tcga-brca-pam50-frozen-research-heatmaps-aligned-adapter) before use.


**Source seals and geometric QA.** Use `rt_read_pam50_locked(st06_file, st07_file, st09_file, expected_sha256)` before plotting actual frozen research sources. It matches three externally reviewed source digests; checks 21,432 gene effects, 128,592 six-family contrast rows, the 60-gene selection and high-effect anchor semantics; and returns selected records only when admission passes. Following local PDF export run `python3 scripts/audit_pam50_layout.py ... --min-margin-pt 12 --check-labels` to check full gene-label presence and glyph bounding boxes. These are structural checks, not scientific approval.


**Color-scale sensitivity without hidden manipulation.** Source `R/research_pam50_scale_diagnostic.R` after `research_plots.R`, `research_pam50_heatmaps.R`, and supply the validated research bundle to `rt_pam50_scale_diagnostic(bundle, neutral_fraction = 0.2)`. It returns a supplementary 2-panel ggplot and tabulated counts/quantiles (240 subtype-effect cells, 360 contrast cells) using the exact shared unclipped main heatmap scale. Export this figure **separately** with `rt_manuscript_export()` and keep its analysis unit as *modeled effect cell*, never patient. The complete code appears in the [manuscript delivery guide](../docs/MANUSCRIPT_VISUALIZATION_DELIVERY.md).


**Caption and accessibility gate:** The PAM50 export includes a visibly labeled categorical `Gene anchor (15 each)` key on each panel and a separate `.caption.txt` companion for journal submission. `rt_pam50_manuscript_caption(bundle, "paired_effects")` / `(..., "six_contrasts")` generates explicit paired-estimand, anchor, contrast-direction, negative/positive color and descriptive-only text; no claim of statistical or clinical validation is added. Keep the caption and its identical metadata alongside private PDF/PNG until author and scientific review. The PDF geometry gate now fails if these are missing or inconsistent.
