# Biomedical R and tidyverse coding contract

**Author: Paul Skeffington · Prepared with OpenAI**

This is the executable convention for all newly authored R scripts, figure helpers, and code examples in this template. It aligns with the repository's [whole-project coding conventions](../docs/CODING_CONVENTIONS.md) and the [official tidyverse style guide](https://style.tidyverse.org/). These are recommended internal conventions, not instructions to overwrite published source schemas.

## Required practices

| Layer | Standard | Example |
| --- | --- | --- |
| Source | Keep original names/units/accession IDs unchanged | `participants_source$Subject_ID` |
| Mapping | Make an explicit, testable source-to-analysis crosswalk | `c(participant_id = "Subject_ID")` |
| Internal names | Lowercase `snake_case`; domain + stage for data frames | `measurements_clean`, `analysis_ready`, `participant_id` |
| Functions | Verb-first `snake_case` with errors and return contract | `validate_join_keys()`, `summarize_measurements()` |
| Data work | Native `|>` and explicit `dplyr::` calls | `data |> dplyr::filter(...) |> dplyr::mutate(...)` |
| Reshaping | `tidyr::pivot_longer()` or `pivot_wider()` | Keep absent values and check expected row counts |
| Joins | Explicit key and relationship; review unmatched/duplicates | `join_research_tables(..., relationship="one-to-one")` |
| Plotting | `ggplot2::ggplot(data, ggplot2::aes(...)) + geom + scale + labs + theme` | `ggplot2::aes(x = .data[[column]])` |
| Variable names in aesthetics | `.data[[name]]` for programmatic functions | Never `aes_string` / implicit global vectors |
| Output | Editable ggplot object; no implicit file writes | `p <- rt_plot(...)`; `rt_save(p, path)` |
| Color | Stable Okabe–Ito category keys, Viridis magnitude, centered diverging | Always mark NA separately |
| Imports | `ggplot2::`, `dplyr::`, `tidyr::`, `tibble::`, `readr::` | Avoid attaching the entire tidyverse within libraries |

Native `|>` pipes make individual transformations visible. Use one intention per pipeline step and break arguments across lines for clarity. Indent continuation consistently; place operators at the ends of lines. Avoid `setwd()`, automatic package installation, `attach()`, global assignment `<<-`, hidden downloads and writing data during `source()`.

## Canonical executable workflow

Run from the repository root, with explicit import order:

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
print(result$figure)
rt_save(result$figure, "artifacts/tidy/relationship.pdf")
~~~

The source-schema demonstration uses `Subject_ID`, `Site`, `Age`, `Marker` *only* in the protected source-naming stage. Internal analysis fields are `participant_id`, `site`, `age_years`, and `measurement_mg_dl`. **Never infer meaning or units from a similarly named external variable.**

## Complete grammar-of-graphics example

~~~r
participants_clean <- result$analysis_ready |>
  dplyr::filter(!is.na(.data$measurement_mg_dl)) |>
  dplyr::mutate(site = factor(
    .data$site, levels = c("North", "South", "West")
  ))

p <- ggplot2::ggplot(
  participants_clean,
  ggplot2::aes(x = .data$site, y = .data$measurement_mg_dl,
               fill = .data$site)
) +
  ggplot2::geom_boxplot(outlier.shape = NA, alpha = 0.75) +
  ggplot2::geom_point(
    position = ggplot2::position_jitter(width = 0.08, seed = 711),
    alpha = 0.40
  ) +
  ggplot2::scale_fill_manual(
    values = stats::setNames(rt_palette()[1:3],
                             c("North", "South", "West"))
  ) +
  ggplot2::labs(
    title = "Synthetic measurements by site",
    x = "Enrollment site (category)",
    y = "Simulated measurement (mg/dL)",
    caption = "Synthetic demonstration; show group denominators in reporting."
  ) +
  rt_theme()
print(p)
~~~

## Canonical data calls

~~~r
source("R/research_tidy.R")
source("R/synthetic_demo.R")
participants_clean <- make_synthetic_cohort(n = 90L, seed = 711L)

summarize_measurements(
  participants_clean, "measurement_mg_dl", "mg/dL", by = "site"
)
summarize_missingness(
  participants_clean, c("age_years", "measurement_mg_dl")
)

measurements_long <- pivot_measurements_longer(
  participants_clean,
  id_columns = c("participant_id", "site"),
  measurement_columns = c("age_years", "measurement_mg_dl"),
  measurement_units = c(age_years = "years", measurement_mg_dl = "mg/dL")
)
measurements_wide <- pivot_measurements_wider(
  measurements_long, id_columns = c("participant_id", "site")
)
~~~

**Design guardrails:** A person, specimen, encounter and visit are distinct analysis units. Repeated visits require composite `participant_id` + `visit_id` keys. Join types must match declared cardinality, with unmatched counts audited. For complex surveys, genomic count models and clinical predictions, choose specialized statistical methods rather than treating tidy formatting as scientific validity.

## Compatibility notes

The older `rt_*` plotting calls remain available, returning editable `ggplot` objects. The primary summary interface is now `summarize_measurements()`, which returns a consistent **tidy tibble**, optionally with `by`. The compatibility `rt_summary_by()` also returns a grouped tibble rather than a list. Include `source("R/research_tidy.R")` **before** sourcing the plotting library.

## Validation

CI installs R, ggplot2, dplyr, tidyr, and tibble, tests full plots and joins/wide-long round trips, and checks the style contract without auto-rewriting files. Python and its documented ML tools remain supported, but R examples should demonstrate data cleaning in tidyverse grammar first.

## Repository-wide enforcement

The [repository coding contract](../docs/CODING_CONVENTIONS.md) distinguishes tidyverse-style R from idiomatic Python. CI discovers every `R/**/*.R` file, checks parseability, snake_case function names, explicit namespaces, native pipes and no source-time execution in reusable modules. A second gate parses complete R examples in Markdown. Existing source identifiers are never renamed by the style checker.

## caret research-classifier extensions

In optional R predictive modeling, use `caret::` and `pROC::` explicit namespaces and keep heavy package dependencies out of module imports. Validate subject and outcome identifiers before group-level holdout splitting. Supply `trainControl(index=...)` with group-disjoint analysis-fold row indices; fold-exclusive imputation and scaling belong in `caret::train(preProcess=...)`. Declare the positive class as the first factor level and repeat it in `confusionMatrix(positive=...)`. Never combine training-fold AUROC and independent holdout accuracy. Return model artifacts without writing or publishing them automatically.

The synthetic design is specified in [R/research_caret.R](research_caret.R) and [caret literature and implementation methods](../docs/CARET_RESEARCH_WORKFLOW.md). Source permissions and all general R naming, import, security and style contracts still apply.
