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
