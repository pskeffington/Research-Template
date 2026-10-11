# End-to-end, synthetic-only tidyverse data-contract regression suite.
source("R/research_tidy.R")
source("R/research_plots.R")
source("R/synthetic_demo.R")
source("R/example_tidy_workflow.R")
result <- run_tidy_example(n = 90L, seed = 711L)

stopifnot(
  inherits(result$participants_clean, "tbl_df"),
  identical(names(result$participants_clean),
            c("participant_id", "site", "age_years", "measurement_mg_dl")),
  nrow(result$id_audit) == 1L,
  result$id_audit$n_distinct_keys == 90L,
  nrow(result$analysis_ready) == 90L,
  result$join_audit$n_after == 90L,
  result$join_audit$n_unmatched_left == 0L,
  result$join_audit$n_unmatched_right == 0L,
  nrow(result$measurements_long) == 180L,
  nrow(result$measurements_wide) == 90L,
  sum(is.na(result$measurements_long$value)) == 10L,
  nrow(result$site_summary) == 3L,
  all(result$site_summary$unit == "mg/dL"),
  nrow(result$missingness_summary) == 2L,
  inherits(result$figure, "ggplot")
)
stopifnot(length(ggplot2::ggplot_build(result$figure)$data) > 0L)

# A real observation-level round trip must preserve IDs, measurements and NA.
original <- result$analysis_ready |>
  dplyr::select(dplyr::all_of(
    c("participant_id", "site", "age_years", "measurement_mg_dl")
  )) |>
  dplyr::arrange(.data$participant_id)
restored <- result$measurements_wide |>
  dplyr::select(dplyr::all_of(names(original))) |>
  dplyr::arrange(.data$participant_id)
stopifnot(isTRUE(all.equal(original, restored, check.attributes = FALSE)))

# Wrong join relationship and missing keys must fail, not silently expand.
duplicates <- dplyr::bind_rows(result$analysis_ready, result$analysis_ready[1, ])
bad_duplicate <- try(validate_join_keys(duplicates, "participant_id"), silent = TRUE)
stopifnot(inherits(bad_duplicate, "try-error"))
bad_join <- try(join_research_tables(
  result$analysis_ready, duplicates, "participant_id", relationship = "one-to-one"
), silent = TRUE)
stopifnot(inherits(bad_join, "try-error"))
bad_key <- result$analysis_ready
bad_key$participant_id[1] <- NA_character_
stopifnot(inherits(
  try(validate_join_keys(bad_key, "participant_id"), silent = TRUE), "try-error"
))

expanded <- join_research_tables(
  result$analysis_ready, duplicates, "participant_id",
  relationship = "one-to-many"
)
stopifnot(nrow(expanded) == 91L, attr(expanded, "join_audit")$n_after == 91L)
bad_mapping <- try(rename_source_columns(
  result$participants_source, c(BadName = "Subject_ID")
), silent = TRUE)
stopifnot(inherits(bad_mapping, "try-error"))
bad_units <- try(pivot_measurements_longer(
  result$analysis_ready, "participant_id",
  c("age_years", "measurement_mg_dl"), c(age_years = "years")
), silent = TRUE)
stopifnot(inherits(bad_units, "try-error"))

cat("Tidy workflow gate: mapping, joins, 180-row pivot, NA, stats, ggplot PASS\n")
