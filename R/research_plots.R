# Independent, reusable biomedical plot functions.
# Author: Paul Skeffington. Prepared with OpenAI.
# No install, external I/O, or plotting when sourced.
# Source R/research_tidy.R before this file for dplyr/tidyr contracts.

rt_palette <- function() {
  c("#0072B2", "#D55E00", "#009E73", "#CC79A7",
    "#E69F00", "#56B4E9", "#000000", "#F0E442")
}

rt_axis_label <- function(name, unit) {
  if (length(name) != 1L || !is.character(name) || is.na(name) ||
      !nzchar(trimws(name)) || length(unit) != 1L ||
      !is.character(unit) || is.na(unit) || !nzchar(trimws(unit)))
    stop("Supply nonempty name and explicit unit (use 'unitless' if appropriate).")
  sprintf("%s (%s)", name, unit)
}

rt_require <- function() {
  require_tidy_tools()
  if (!requireNamespace("ggplot2", quietly = TRUE))
    stop("ggplot2 required; restore it in your approved R environment.")
}

rt_theme <- function() {
  rt_require()
  ggplot2::theme_classic(base_size = 12) +
    ggplot2::theme(
      plot.title = ggplot2::element_text(face = "bold", colour = "#14233B"),
      plot.subtitle = ggplot2::element_text(colour = "#3D4D60"),
      plot.caption = ggplot2::element_text(colour = "#5B6374", hjust = 0),
      legend.position = "bottom",
      axis.title = ggplot2::element_text(colour = "#293548")
    )
}

rt_numeric <- function(data, column) {
  if (!is.data.frame(data) || !column %in% names(data) ||
      !is.numeric(data[[column]]) ||
      any(is.infinite(data[[column]])))
    stop("Expected a numeric column; infinite values are forbidden.")
  data[[column]][is.finite(data[[column]])]
}

rt_summary <- function(data, column, unit) {
  # Compatibility call; the documented tidy result is a one-row tibble.
  summarize_measurements(data, measurement = column, unit = unit)
}

rt_summary_by <- function(data, value, group, unit, levels = NULL) {
  if (!group %in% names(data)) stop("Group column required.")
  if (!is.null(levels) && (!is.character(levels) || anyDuplicated(levels) ||
                          !all(stats::na.omit(data[[group]]) %in% levels))) {
    stop("Declared category levels must uniquely cover observed categories.")
  }
  prepared <- tibble::as_tibble(data)
  if (!is.null(levels)) {
    prepared <- prepared |>
      dplyr::mutate(dplyr::across(
        dplyr::all_of(group), ~ factor(as.character(.x), levels = levels)
      ))
  }
  summarize_measurements(prepared, measurement = value, unit = unit, by = group)
}

rt_hist <- function(data, value, name, unit, bins = 12L) {
  rt_require()
  measured <- rt_numeric(data, value)
  if (!length(measured) || bins < 2L) stop("Need measured values and >=2 bins.")
  clean <- data |>
    dplyr::filter(!is.na(.data[[value]]))
  counts <- rt_summary(data, value, unit)
  ggplot2::ggplot(clean, ggplot2::aes(x = .data[[value]])) +
    ggplot2::geom_histogram(bins = bins, fill = rt_palette()[1],
                           color = "white", linewidth = 0.35) +
    ggplot2::geom_vline(xintercept = counts$median, color = rt_palette()[2],
                       linetype = "dashed", linewidth = 0.8) +
    ggplot2::labs(
      title = paste(name, "distribution"),
      subtitle = sprintf("Measured n = %d/%d; median = %.2f %s",
                         nrow(clean), nrow(data), counts$median, unit),
      x = rt_axis_label(name, unit), y = "Observations (count)",
      caption = "Unweighted descriptive histogram; missing observations excluded."
    ) + rt_theme()
}

rt_scatter <- function(data, x, y, x_name, x_unit, y_name, y_unit) {
  rt_require()
  rt_numeric(data, x)
  rt_numeric(data, y)
  clean <- data |>
    dplyr::filter(!is.na(.data[[x]]), !is.na(.data[[y]]))
  if (!nrow(clean)) stop("No finite complete pairs.")
  ggplot2::ggplot(clean, ggplot2::aes(x = .data[[x]], y = .data[[y]])) +
    ggplot2::geom_point(color = rt_palette()[1], alpha = 0.76, size = 1.8) +
    ggplot2::labs(
      title = paste(y_name, "versus", x_name),
      subtitle = sprintf("Complete pairs n = %d/%d", nrow(clean), nrow(data)),
      x = rt_axis_label(x_name, x_unit), y = rt_axis_label(y_name, y_unit),
      caption = "Descriptive association; no inferred regression or causal effect."
    ) + rt_theme()
}

rt_group_plot <- function(data, group, value, y_name, y_unit,
                          violin = FALSE, levels = NULL) {
  rt_require()
  rt_numeric(data, value)
  if (!group %in% names(data)) stop("Group column required.")
  clean <- data |>
    dplyr::filter(!is.na(.data[[group]]), !is.na(.data[[value]]))
  if (is.null(levels)) levels <- sort(unique(as.character(clean[[group]])))
  if (length(levels) < 2L || length(levels) > 8L ||
      anyDuplicated(levels) || !all(as.character(clean[[group]]) %in% levels))
    stop("Declared levels must cover 2–8 unique groups.")
  clean <- clean |>
    dplyr::mutate(dplyr::across(
      dplyr::all_of(group), ~ factor(as.character(.x), levels = levels)
    ))
  counts <- table(clean[[group]])
  if (any(counts < 2)) stop("Each group requires >=2 complete observations.")
  p <- ggplot2::ggplot(clean, ggplot2::aes(
    x = .data[[group]], y = .data[[value]], fill = .data[[group]]
  ))
  if (violin) {
    p <- p + ggplot2::geom_violin(alpha = 0.65, trim = FALSE) +
      ggplot2::stat_summary(fun = median, geom = "point", color = "#111827", size = 2)
  } else {
    p <- p + ggplot2::geom_boxplot(alpha = 0.76, outlier.shape = NA) +
      ggplot2::geom_jitter(width = 0.12, alpha = 0.42, size = 1.1)
  }
  p + ggplot2::scale_fill_manual(
    values = stats::setNames(rt_palette()[seq_along(levels)], levels), drop = FALSE,
    name = paste(group, "(category)")
  ) + ggplot2::labs(
    title = paste(y_name, "by", group),
    subtitle = paste(paste(names(counts), as.integer(counts), sep = " n="), collapse = "; "),
    x = paste(group, "(category)"), y = rt_axis_label(y_name, y_unit),
    caption = if (violin)
      "Smoothed descriptive distributions; sample size affects shape." else
      "Median/quartile boxes; whiskers are not confidence intervals."
  ) + rt_theme()
}

rt_box <- function(data, group, value, y_name, y_unit, levels = NULL) {
  rt_group_plot(data, group, value, y_name, y_unit, levels = levels)
}

rt_violin <- function(data, group, value, y_name, y_unit, levels = NULL) {
  rt_group_plot(data, group, value, y_name, y_unit,
                violin = TRUE, levels = levels)
}

rt_bar <- function(data, group, levels = NULL) {
  rt_require()
  if (!group %in% names(data)) stop("Unknown group.")
  clean <- data |>
    dplyr::filter(!is.na(.data[[group]]))
  if (is.null(levels)) levels <- sort(unique(as.character(clean[[group]])))
  if (length(levels) < 2L || length(levels) > 8L ||
      !all(as.character(clean[[group]]) %in% levels))
    stop("Expected 2–8 declared categories.")
  clean[[group]] <- factor(as.character(clean[[group]]), levels = levels)
  ggplot2::ggplot(clean, ggplot2::aes(x = .data[[group]], fill = .data[[group]])) +
    ggplot2::geom_bar(color = "#313E4A", linewidth = 0.4) +
    ggplot2::geom_text(stat = "count", ggplot2::aes(label = ggplot2::after_stat(count)),
                      vjust = -0.4) +
    ggplot2::scale_fill_manual(
      values = stats::setNames(rt_palette()[seq_along(levels)], levels), drop = FALSE
    ) + ggplot2::scale_y_continuous(expand = ggplot2::expansion(mult = c(0, 0.12))) +
    ggplot2::labs(
      title = paste(group, "category counts"),
      subtitle = sprintf("Known categories n=%d/%d; missing=%d",
                         nrow(clean), nrow(data), nrow(data) - nrow(clean)),
      x = paste(group, "(category)"), y = "Observations (count)",
      caption = "Raw observed counts; no weighting or inferred group difference."
    ) + rt_theme()
}

rt_heatmap <- function(x, row_labels, col_labels, name, unit,
                       mode = c("sequential", "diverging"), center = NULL) {
  rt_require()
  mode <- match.arg(mode)
  if (!is.matrix(x) || !is.numeric(x) || any(is.infinite(x)) ||
      all(is.na(x)) || nrow(x) != length(row_labels) ||
      ncol(x) != length(col_labels) || anyDuplicated(row_labels) ||
      anyDuplicated(col_labels) || anyNA(row_labels) || anyNA(col_labels)) {
    stop("Numeric matrix with finite cells, unique aligned labels required.")
  }
  if (mode == "diverging" &&
      (is.null(center) || length(center) != 1L || !is.finite(center))) {
    stop("Diverging mode requires explicit finite scientific center.")
  }
  if (mode == "sequential" && !is.null(center)) {
    stop("Sequential mode does not accept center.")
  }
  rt_axis_label(name, unit)

  # Matrix orientation: rows are features, columns are samples.
  # Pivot explicitly rather than silently flattening by column order.
  wide <- tibble::as_tibble(x, .name_repair = "minimal")
  names(wide) <- col_labels
  long <- wide |>
    dplyr::mutate(feature_id = row_labels, .before = 1) |>
    tidyr::pivot_longer(
      cols = dplyr::all_of(col_labels),
      names_to = "sample_id",
      values_to = "value",
      values_drop_na = FALSE
    ) |>
    dplyr::mutate(
      feature_id = factor(.data$feature_id, levels = rev(row_labels)),
      sample_id = factor(.data$sample_id, levels = col_labels)
    )
  p <- ggplot2::ggplot(
    long,
    ggplot2::aes(x = .data$sample_id, y = .data$feature_id, fill = .data$value)
  ) +
    ggplot2::geom_tile(color = "#F5F6F8", linewidth = 0.2) +
    ggplot2::labs(
      title = name,
      subtitle = sprintf("%d features x %d samples | missing cells=%d",
                         nrow(x), ncol(x), sum(is.na(x))),
      x = "Sample identifier", y = "Feature identifier",
      caption = if (mode == "diverging") {
        paste("Signed deviation; center =", center, unit, "| missing in gray.")
      } else {
        "Sequential magnitude; missing cells in gray."
      }
    ) +
    rt_theme() +
    ggplot2::theme(axis.text.x = ggplot2::element_text(angle = 90, hjust = 1))
  if (mode == "sequential") {
    return(p + ggplot2::scale_fill_viridis_c(
      name = rt_axis_label(name, unit), na.value = "#CED4DC"
    ))
  }
  limit <- max(abs(x - center), na.rm = TRUE)
  if (limit == 0) limit <- 1
  p + ggplot2::scale_fill_gradient2(
    name = rt_axis_label(name, unit),
    low = "#2166AC", mid = "#F7F7F7", high = "#B2182B",
    midpoint = center, limits = c(center - limit, center + limit),
    na.value = "#CED4DC"
  )
}

rt_corr_heatmap <- function(data, columns) {
  rt_require()
  if (length(columns) < 2L || anyDuplicated(columns)) {
    stop("Select two or more distinct numeric variables.")
  }
  for (column in columns) rt_numeric(data, column)
  numeric_data <- data |>
    dplyr::select(dplyr::all_of(columns))
  observed <- as.matrix(numeric_data)
  coefficients <- stats::cor(
    observed, use = "pairwise.complete.obs", method = "pearson"
  )
  counts <- outer(
    seq_along(columns), seq_along(columns),
    Vectorize(function(i, j) {
      sum(stats::complete.cases(observed[, c(i, j)]))
    })
  )
  coefficients_wide <- tibble::as_tibble(coefficients, .name_repair = "minimal")
  counts_wide <- tibble::as_tibble(counts, .name_repair = "minimal")
  names(coefficients_wide) <- columns
  names(counts_wide) <- columns
  coefficient_long <- coefficients_wide |>
    dplyr::mutate(variable_y = columns, .before = 1) |>
    tidyr::pivot_longer(
      cols = dplyr::all_of(columns), names_to = "variable_x",
      values_to = "pearson_r"
    )
  counts_long <- counts_wide |>
    dplyr::mutate(variable_y = columns, .before = 1) |>
    tidyr::pivot_longer(
      cols = dplyr::all_of(columns), names_to = "variable_x",
      values_to = "n_pair"
    )
  long <- dplyr::left_join(
    coefficient_long, counts_long, by = c("variable_x", "variable_y")
  ) |>
    dplyr::mutate(
      variable_x = factor(.data$variable_x, levels = columns),
      variable_y = factor(.data$variable_y, levels = rev(columns)),
      label = ifelse(is.na(.data$pearson_r),
                     paste0("NA\nn=", .data$n_pair),
                     sprintf("%.2f\nn=%d", .data$pearson_r, .data$n_pair))
    )
  ggplot2::ggplot(
    long, ggplot2::aes(
      x = .data$variable_x, y = .data$variable_y, fill = .data$pearson_r
    )
  ) +
    ggplot2::geom_tile(color = "#F3F4F6") +
    ggplot2::geom_text(ggplot2::aes(label = .data$label), size = 3) +
    ggplot2::scale_fill_gradient2(
      limits = c(-1, 1), midpoint = 0,
      low = "#2166AC", mid = "#F7F7F7", high = "#B2182B",
      na.value = "#CED4DC", name = "Pearson r (unitless)"
    ) +
    ggplot2::labs(
      title = "Pearson correlation matrix",
      subtitle = "Pairwise complete cases; n reported in each cell",
      x = "Variable", y = "Variable",
      caption = "Descriptive associations; no p-values or causal claims."
    ) +
    rt_theme() +
    ggplot2::theme(axis.text.x = ggplot2::element_text(angle = 45, hjust = 1))
}

rt_kit <- function(data, variables, study, observation_unit, source,
                   status = "SYNTHETIC / DESCRIPTIVE ONLY") {
  rt_require()
  if (!is.data.frame(data) || !nrow(data) ||
      !is.list(variables) || !length(variables) ||
      !all(names(variables) %in% names(data)) ||
      any(!nzchar(c(study, observation_unit, source, status))))
    stop("Provide data, named dictionary and complete study metadata.")
  for (key in names(variables)) {
    spec <- variables[[key]]
    if (is.null(spec$label) || is.null(spec$unit))
      stop(paste("Missing label/unit for", key))
    rt_axis_label(spec$label, spec$unit)
  }
  structure(list(data = data, variables = variables, study = study,
                 observation_unit = observation_unit, source = source,
                 status = status), class = "rt_kit")
}

rt_plot <- function(kit, kind, value = NULL, x = NULL, y = NULL, group = NULL,
                    bins = 12L) {
  if (!inherits(kit, "rt_kit")) stop("Create rt_kit() with declared metadata first.")
  fields <- unique(Filter(Negate(is.null), list(value, x, y, group)))
  if (!all(unlist(fields) %in% names(kit$variables)))
    stop("Every plotted field must have a dictionary label and unit.")
  get <- function(col) kit$variables[[col]]
  data <- tibble::as_tibble(kit$data)
  p <- switch(kind,
    hist = rt_hist(data, value, get(value)$label, get(value)$unit, bins),
    box = rt_box(data, group, value, get(value)$label, get(value)$unit,
                 levels = get(group)$levels),
    violin = rt_violin(data, group, value, get(value)$label, get(value)$unit,
                       levels = get(group)$levels),
    scatter = rt_scatter(data, x, y, get(x)$label, get(x)$unit,
                         get(y)$label, get(y)$unit),
    bar = rt_bar(data, group, levels = get(group)$levels),
    stop("Choose hist, box, violin, scatter or bar.")
  )
  p + ggplot2::labs(
    tag = paste(kit$study, "|", kit$observation_unit),
    caption = paste(p$labels$caption, "\nSource:", kit$source, "|", kit$status)
  )
}

rt_save <- function(plot, path, width = 7, height = 5, dpi = 300) {
  rt_require()
  if (!inherits(plot, "ggplot")) stop("Expected a ggplot object.")
  if (!grepl("\\.(png|pdf|svg)$", path, ignore.case = TRUE))
    stop("Use png, pdf or svg extension.")
  dir.create(dirname(path), recursive = TRUE, showWarnings = FALSE)
  ggplot2::ggsave(
    filename = path, plot = plot, width = width, height = height,
    units = "in", dpi = dpi, bg = "white"
  )
  invisible(path)
}
