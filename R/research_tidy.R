# Reusable tidy biomedical data contracts, independently authored.
# Author: Paul Skeffington. Prepared with OpenAI.
# Source defines functions only; no installs, network, data reads or writes.
# Preserve original data source codes until a documented source-to-analysis rename.

require_tidy_tools <- function() {
  packages <- c("dplyr", "tidyr", "tibble")
  missing_packages <- packages[!vapply(
    packages, requireNamespace, quietly = TRUE, FUN.VALUE = logical(1)
  )]
  if (length(missing_packages)) {
    stop(
      "Restore required R packages in the approved environment: ",
      paste(missing_packages, collapse = ", "),
      call. = FALSE
    )
  }
  invisible(TRUE)
}

validate_research_columns <- function(data, columns) {
  require_tidy_tools()
  if (!is.data.frame(data) || !is.character(columns) || !length(columns) ||
      anyNA(columns) || anyDuplicated(columns) ||
      any(!nzchar(columns)) || !all(columns %in% names(data))) {
    stop("Expected a data frame with all requested unique column names.", call. = FALSE)
  }
  invisible(TRUE)
}

validate_join_keys <- function(data, keys, require_unique = TRUE) {
  validate_research_columns(data, keys)
  if (any(!stats::complete.cases(dplyr::select(data, dplyr::all_of(keys))))) {
    stop("Missing join key; investigate source records before joining.", call. = FALSE)
  }
  keys_by_group <- data |>
    dplyr::group_by(dplyr::across(dplyr::all_of(keys))) |>
    dplyr::summarise(n_key = dplyr::n(), .groups = "drop")
  duplicates <- keys_by_group |>
    dplyr::filter(.data$n_key > 1L)
  if (require_unique && nrow(duplicates)) {
    stop("Duplicate keys violate the declared join relationship.", call. = FALSE)
  }
  tibble::tibble(
    n_rows = nrow(data),
    n_distinct_keys = nrow(keys_by_group),
    n_duplicated_keys = nrow(duplicates),
    n_extra_duplicate_rows = sum(duplicates$n_key - 1L)
  )
}

rename_source_columns <- function(source_data, source_to_analysis) {
  # Named mapping: c(participant_id = "Subject_ID", age_years = "Age").
  # Original source names remain unchanged in the raw data layer.
  require_tidy_tools()
  if (!is.data.frame(source_data) ||
      !is.character(source_to_analysis) ||
      !length(source_to_analysis) ||
      is.null(names(source_to_analysis)) ||
      anyNA(source_to_analysis) || anyDuplicated(source_to_analysis) ||
      anyDuplicated(names(source_to_analysis)) ||
      !all(source_to_analysis %in% names(source_data)) ||
      !all(grepl("^[a-z][a-z0-9]*(?:_[a-z0-9]+)*$",
                 names(source_to_analysis)))) {
    stop("Provide a complete source-to-snake_case mapping for existing columns.",
         call. = FALSE)
  }
  dplyr::rename(tibble::as_tibble(source_data), dplyr::all_of(source_to_analysis))
}

join_research_tables <- function(left, right, keys,
                                 relationship = c("one-to-one", "one-to-many", "many-to-one"),
                                 join = c("left", "inner")) {
  require_tidy_tools()
  relationship <- match.arg(relationship)
  join <- match.arg(join)
  # This pre-validates cardinality independently of dplyr's installed version.
  left_unique <- relationship %in% c("one-to-one", "one-to-many")
  right_unique <- relationship %in% c("one-to-one", "many-to-one")
  left_keys <- validate_join_keys(left, keys, require_unique = left_unique)
  right_keys <- validate_join_keys(right, keys, require_unique = right_unique)
  n_unmatched_left <- nrow(dplyr::anti_join(left, right, by = keys))
  n_unmatched_right <- nrow(dplyr::anti_join(right, left, by = keys))
  result <- if (join == "left") {
    dplyr::left_join(left, right, by = keys)
  } else {
    dplyr::inner_join(left, right, by = keys)
  }
  audit <- tibble::tibble(
    join_type = join,
    relationship = relationship,
    n_left = nrow(left),
    n_right = nrow(right),
    n_after = nrow(result),
    n_unmatched_left = n_unmatched_left,
    n_unmatched_right = n_unmatched_right,
    n_unique_left = left_keys$n_distinct_keys,
    n_unique_right = right_keys$n_distinct_keys
  )
  attr(result, "join_audit") <- audit
  result
}

pivot_measurements_longer <- function(data, id_columns, measurement_columns,
                                      measurement_units,
                                      measurement_name = "measurement",
                                      value_name = "value") {
  require_tidy_tools()
  validate_research_columns(data, c(id_columns, measurement_columns))
  validate_join_keys(data, id_columns, require_unique = TRUE)
  if (!is.character(measurement_units) ||
      is.null(names(measurement_units)) ||
      !setequal(names(measurement_units), measurement_columns) ||
      anyNA(measurement_units) || any(!nzchar(measurement_units)) ||
      any(c(measurement_name, value_name, "unit") %in% names(data)) ||
      anyDuplicated(c(measurement_name, value_name, "unit")) ||
      !all(grepl("^[a-z][a-z0-9_]*$", c(measurement_name, value_name)))) {
    stop("Specify one explicit unit per measurement and noncolliding tidy names.",
         call. = FALSE)
  }
  result <- data |>
    tibble::as_tibble() |>
    tidyr::pivot_longer(
      cols = dplyr::all_of(measurement_columns),
      names_to = measurement_name,
      values_to = value_name,
      values_drop_na = FALSE
    ) |>
    dplyr::mutate(unit = unname(measurement_units[.data[[measurement_name]]]))
  expected_n <- nrow(data) * length(measurement_columns)
  if (nrow(result) != expected_n || anyNA(result$unit)) {
    stop("Wide-to-long row-count or unit mapping contract failed.", call. = FALSE)
  }
  result
}

pivot_measurements_wider <- function(data, id_columns,
                                     measurement_name = "measurement",
                                     value_name = "value") {
  require_tidy_tools()
  validate_research_columns(data, c(id_columns, measurement_name, value_name))
  validate_join_keys(data, c(id_columns, measurement_name), require_unique = TRUE)
  data |>
    dplyr::select(dplyr::all_of(c(id_columns, measurement_name, value_name))) |>
    tidyr::pivot_wider(
      id_cols = dplyr::all_of(id_columns),
      names_from = dplyr::all_of(measurement_name),
      values_from = dplyr::all_of(value_name)
    )
}

summarize_measurements <- function(data, measurement, unit, by = NULL) {
  require_tidy_tools()
  validate_research_columns(data, c(measurement, by))
  if (!is.numeric(data[[measurement]]) ||
      any(is.infinite(data[[measurement]])) ||
      !is.character(unit) || length(unit) != 1L ||
      is.na(unit) || !nzchar(trimws(unit))) {
    stop("Measurement must be finite numeric/NA with a declared unit.",
         call. = FALSE)
  }
  prepared <- tibble::as_tibble(data)
  if (!is.null(by)) {
    prepared <- prepared |>
      dplyr::group_by(dplyr::across(dplyr::all_of(by)), .drop = FALSE)
  }
  result <- prepared |>
    dplyr::summarise(
      n_total = dplyr::n(),
      n_measured = sum(!is.na(.data[[measurement]])),
      n_missing = sum(is.na(.data[[measurement]])),
      mean = if (all(is.na(.data[[measurement]]))) NA_real_ else
        mean(.data[[measurement]], na.rm = TRUE),
      sd = if (sum(!is.na(.data[[measurement]])) < 2L) NA_real_ else
        stats::sd(.data[[measurement]], na.rm = TRUE),
      median = if (all(is.na(.data[[measurement]]))) NA_real_ else
        stats::median(.data[[measurement]], na.rm = TRUE),
      q1 = if (all(is.na(.data[[measurement]]))) NA_real_ else
        as.numeric(stats::quantile(.data[[measurement]], 0.25, na.rm = TRUE)),
      q3 = if (all(is.na(.data[[measurement]]))) NA_real_ else
        as.numeric(stats::quantile(.data[[measurement]], 0.75, na.rm = TRUE)),
      minimum = if (all(is.na(.data[[measurement]]))) NA_real_ else
        min(.data[[measurement]], na.rm = TRUE),
      maximum = if (all(is.na(.data[[measurement]]))) NA_real_ else
        max(.data[[measurement]], na.rm = TRUE),
      .groups = "drop"
    ) |>
    dplyr::mutate(
      variable = measurement,
      unit = unit,
      missing_pct = ifelse(.data$n_total > 0L,
                           100 * .data$n_missing / .data$n_total, NA_real_),
      iqr = .data$q3 - .data$q1
    )
  result
}

summarize_missingness <- function(data, columns) {
  validate_research_columns(data, columns)
  data |>
    dplyr::summarise(
      dplyr::across(dplyr::all_of(columns), ~ sum(is.na(.x)))
    ) |>
    tidyr::pivot_longer(
      cols = dplyr::all_of(columns),
      names_to = "variable",
      values_to = "n_missing"
    ) |>
    dplyr::mutate(
      n_total = nrow(data),
      missing_pct = 100 * .data$n_missing / .data$n_total
    )
}
