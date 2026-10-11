# Original, optional scientific plotting helpers.
# Author: Paul Skeffington. Prepared with OpenAI.
# No package install, external I/O, or plotting when sourced.

rt_palette <- function() {
  c("#0072B2", "#D55E00", "#009E73", "#CC79A7",
    "#E69F00", "#56B4E9", "#000000", "#F0E442")
}

rt_axis_label <- function(name, unit) {
  if (length(name) != 1L || !is.character(name) || is.na(name) ||
      !nzchar(trimws(name)) || length(unit) != 1L ||
      !is.character(unit) || is.na(unit) || !nzchar(trimws(unit)))
    stop("Supply nonempty name and explicit unit (use 'unitless' if appropriate).")
  paste0(name, " (", unit, ")")
}

rt_require <- function() {
  if (!requireNamespace("ggplot2", quietly = TRUE))
    stop("ggplot2 required: install separately in approved environment.")
}

rt_scatter <- function(data, x, y, x_name, x_unit, y_name, y_unit) {
  rt_require()
  if (!all(c(x, y) %in% names(data))) stop("Unknown x or y column.")
  if (!is.numeric(data[[x]]) || !is.numeric(data[[y]]))
    stop("x and y must be numeric.")
  clean <- data[is.finite(data[[x]]) & is.finite(data[[y]]), , drop = FALSE]
  if (nrow(clean) == 0L) stop("No finite complete pairs.")
  ggplot2::ggplot(clean, ggplot2::aes(x = .data[[x]], y = .data[[y]])) +
    ggplot2::geom_point(color = rt_palette()[1], alpha = 0.7) +
    ggplot2::labs(title = paste(y_name, "versus", x_name),
      subtitle = sprintf("Complete pairs n = %d / %d", nrow(clean), nrow(data)),
      x = rt_axis_label(x_name, x_unit), y = rt_axis_label(y_name, y_unit),
      caption = "Synthetic/descriptive workflow; no causal inference.") +
    ggplot2::theme_classic(base_size = 12)
}

rt_box <- function(data, group, value, y_name, y_unit) {
  rt_require()
  if (!all(c(group, value) %in% names(data))) stop("Unknown group or value.")
  if (!is.numeric(data[[value]])) stop("value must be numeric.")
  clean <- data[!is.na(data[[group]]) & is.finite(data[[value]]), , drop = FALSE]
  groups <- sort(unique(as.character(clean[[group]])))
  if (length(groups) < 2L || length(groups) > 8L) stop("2 to 8 groups required.")
  clean[[group]] <- factor(as.character(clean[[group]]), levels = groups)
  counts <- table(clean[[group]])
  ggplot2::ggplot(clean, ggplot2::aes(x = .data[[group]], y = .data[[value]],
                                     fill = .data[[group]])) +
    ggplot2::geom_boxplot(outlier.shape = NA, alpha = 0.7) +
    ggplot2::geom_jitter(width = 0.12, alpha = 0.45, size = 1.2) +
    ggplot2::scale_fill_manual(values = stats::setNames(rt_palette()[seq_along(groups)], groups),
                               name = group) +
    ggplot2::labs(title = paste(y_name, "by", group),
      subtitle = paste(paste(names(counts), as.integer(counts), sep = ": n="), collapse = "; "),
      x = paste(group, "(category)"), y = rt_axis_label(y_name, y_unit),
      caption = "Descriptive boxplots; whiskers are not confidence intervals.") +
    ggplot2::theme_classic(base_size = 12)
}

rt_heatmap <- function(x, row_labels, col_labels, name, unit,
                       mode = c("sequential", "diverging")) {
  rt_require()
  mode <- match.arg(mode)
  if (!is.matrix(x) || !is.numeric(x) || any(!is.finite(x)) ||
      nrow(x) != length(row_labels) || ncol(x) != length(col_labels))
    stop("Finite numeric matrix with matching row/column labels required.")
  long <- expand.grid(row = seq_len(nrow(x)), col = seq_len(ncol(x)))
  long$value <- as.vector(x)
  p <- ggplot2::ggplot(long, ggplot2::aes(x = .data$col, y = .data$row,
                                        fill = .data$value)) +
    ggplot2::geom_tile() +
    ggplot2::scale_x_continuous(breaks = seq_along(col_labels), labels = col_labels) +
    ggplot2::scale_y_reverse(breaks = seq_along(row_labels), labels = row_labels) +
    ggplot2::labs(title = name, x = "Sample (identifier)", y = "Feature (identifier)") +
    ggplot2::theme_classic(base_size = 12) +
    ggplot2::theme(axis.text.x = ggplot2::element_text(angle = 90, hjust = 1))
  if (mode == "sequential") {
    p + ggplot2::scale_fill_viridis_c(name = rt_axis_label(name, unit))
  } else {
    limit <- max(abs(x))
    if (limit == 0) limit <- 1
    p + ggplot2::scale_fill_gradient2(name = rt_axis_label(name, unit),
      low = "#2166AC", mid = "#F7F7F7", high = "#B2182B", midpoint = 0,
      limits = c(-limit, limit))
  }
}

rt_save <- function(plot, path, width = 7, height = 5, dpi = 300) {
  rt_require()
  if (!inherits(plot, "ggplot")) stop("Expected a ggplot object.")
  if (!grepl("\\.(png|pdf|svg)$", path, ignore.case = TRUE))
    stop("Use png, pdf or svg extension.")
  dir.create(dirname(path), recursive = TRUE, showWarnings = FALSE)
  ggplot2::ggsave(filename = path, plot = plot, width = width, height = height,
                  units = "in", dpi = dpi)
  invisible(path)
}
