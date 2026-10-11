# Independent, reusable biomedical plot functions.
# Author: Paul Skeffington. Prepared with OpenAI.
# No install, external I/O, or plotting when sourced.

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
  rt_axis_label(column, unit)
  measured <- rt_numeric(data, column)
  if (!length(measured)) stop("No finite measurements.")
  q <- stats::quantile(measured, c(0.25, 0.5, 0.75), names = FALSE)
  data.frame(
    variable = column, unit = unit, n_total = nrow(data),
    n_measured = length(measured), n_missing = nrow(data) - length(measured),
    missing_pct = 100 * (nrow(data) - length(measured)) / nrow(data),
    mean = mean(measured),
    sd = if (length(measured) > 1L) stats::sd(measured) else NA_real_,
    median = q[2], q1 = q[1], q3 = q[3], iqr = q[3] - q[1],
    minimum = min(measured), maximum = max(measured)
  )
}

rt_summary_by <- function(data, value, group, unit, levels = NULL) {
  if (!group %in% names(data)) stop("Group column required.")
  if (is.null(levels)) levels <- sort(unique(as.character(stats::na.omit(data[[group]]))))
  if (anyDuplicated(levels) || any(!nzchar(levels))) stop("Unique group levels required.")
  lapply(levels, function(level) {
    subset <- data[!is.na(data[[group]]) & as.character(data[[group]]) == level, ,
                   drop = FALSE]
    if (!nrow(subset)) return(data.frame(group = level, n_total = 0L,
                                         n_measured = 0L, n_missing = 0L))
    cbind(group = level, rt_summary(subset, value, unit))
  })
}

rt_hist <- function(data, value, name, unit, bins = 12L) {
  rt_require()
  measured <- rt_numeric(data, value)
  if (!length(measured) || bins < 2L) stop("Need measured values and >=2 bins.")
  clean <- data[is.finite(data[[value]]), , drop = FALSE]
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
  rt_numeric(data, x); rt_numeric(data, y)
  clean <- data[is.finite(data[[x]]) & is.finite(data[[y]]), , drop = FALSE]
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
  clean <- data[!is.na(data[[group]]) & is.finite(data[[value]]), , drop = FALSE]
  if (is.null(levels)) levels <- sort(unique(as.character(clean[[group]])))
  if (length(levels) < 2L || length(levels) > 8L ||
      anyDuplicated(levels) || !all(as.character(clean[[group]]) %in% levels))
    stop("Declared levels must cover 2–8 unique groups.")
  clean[[group]] <- factor(as.character(clean[[group]]), levels = levels)
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
  clean <- data[!is.na(data[[group]]), , drop = FALSE]
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
      ncol(x) != length(col_labels))
    stop("Numeric matrix with finite observed cells and aligned labels required.")
  if (mode == "diverging" &&
      (is.null(center) || length(center) != 1L || !is.finite(center)))
    stop("Diverging mode requires explicit finite scientific center.")
  if (mode == "sequential" && !is.null(center))
    stop("Sequential mode does not accept center.")
  rt_axis_label(name, unit)
  long <- expand.grid(row = seq_len(nrow(x)), col = seq_len(ncol(x)))
  long$value <- as.vector(x)
  p <- ggplot2::ggplot(long, ggplot2::aes(
    x = .data$col, y = .data$row, fill = .data$value
  )) + ggplot2::geom_tile(color = "#F5F6F8", linewidth = 0.2) +
    ggplot2::scale_x_continuous(breaks = seq_along(col_labels), labels = col_labels) +
    ggplot2::scale_y_reverse(breaks = seq_along(row_labels), labels = row_labels) +
    ggplot2::labs(
      title = name,
      subtitle = sprintf("%d features x %d samples | missing cells=%d",
                         nrow(x), ncol(x), sum(is.na(x))),
      x = "Sample identifier", y = "Feature identifier",
      caption = if (mode == "diverging") paste("Signed deviation; center =", center, unit,
                                               "| missing in gray.") else
                "Sequential magnitude; missing cells in gray."
    ) + rt_theme() +
    ggplot2::theme(axis.text.x = ggplot2::element_text(angle = 90, hjust = 1))
  if (mode == "sequential") {
    p + ggplot2::scale_fill_viridis_c(
      name = rt_axis_label(name, unit), na.value = "#CED4DC"
    )
  } else {
    limit <- max(abs(x - center), na.rm = TRUE)
    if (limit == 0) limit <- 1
    p + ggplot2::scale_fill_gradient2(
      name = rt_axis_label(name, unit),
      low = "#2166AC", mid = "#F7F7F7", high = "#B2182B",
      midpoint = center, limits = c(center - limit, center + limit),
      na.value = "#CED4DC"
    )
  }
}

rt_corr_heatmap <- function(data, columns) {
  rt_require()
  if (length(columns) < 2L || anyDuplicated(columns)) stop("2+ distinct columns required.")
  for (column in columns) rt_numeric(data, column)
  x <- as.matrix(data[columns])
  r <- stats::cor(x, use = "pairwise.complete.obs", method = "pearson")
  counts <- outer(seq_along(columns), seq_along(columns),
                  Vectorize(function(i, j) sum(stats::complete.cases(x[, c(i, j)]))))
  long <- expand.grid(x = seq_along(columns), y = seq_along(columns))
  long$r <- as.vector(r)
  long$n <- as.vector(counts)
  ggplot2::ggplot(long, ggplot2::aes(x = .data$x, y = .data$y, fill = .data$r)) +
    ggplot2::geom_tile(color = "#F3F4F6") +
    ggplot2::geom_text(ggplot2::aes(
      label = ifelse(is.na(.data$r), paste0("NA\nn=", .data$n),
                     sprintf("%.2f\nn=%d", .data$r, .data$n))
    ), size = 3) +
    ggplot2::scale_x_continuous(breaks = seq_along(columns), labels = columns) +
    ggplot2::scale_y_reverse(breaks = seq_along(columns), labels = columns) +
    ggplot2::scale_fill_gradient2(
      limits = c(-1, 1), midpoint = 0, low = "#2166AC",
      mid = "#F7F7F7", high = "#B2182B",
      na.value = "#CED4DC", name = "Pearson r (unitless)"
    ) +
    ggplot2::labs(title = "Pearson correlation matrix",
                  subtitle = "Pairwise complete cases; n shown in every cell",
                  x = "Variable", y = "Variable",
                  caption = "No p-values, causal conclusions or multiple-testing claims.") +
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
  data <- kit$data
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
