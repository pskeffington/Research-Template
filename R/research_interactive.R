# Opt-in interactive visualizations and explicit condition ordering.
# Author: Paul Skeffington. Prepared with OpenAI.
# No installation, file output or browser calls on source.

rt_interactive <- function(plot, tooltip = NULL) {
  if (!inherits(plot, "ggplot")) stop("Expected ggplot object.")
  if (!requireNamespace("plotly", quietly = TRUE))
    stop("Install approved optional plotly before interactive conversion.")
  if (!is.null(tooltip) &&
      (!is.character(tooltip) || anyNA(tooltip)))
    stop("Tooltip must be a character vector.")
  # Review hover fields and sample identifiers before any public export.
  plotly::ggplotly(plot, tooltip = if (is.null(tooltip)) "none" else tooltip)
}

rt_save_interactive <- function(widget, path, data_status,
                                public_release_approved = FALSE,
                                selfcontained = FALSE) {
  if (!inherits(widget, "htmlwidget") || !inherits(widget, "plotly"))
    stop("Expected a plotly htmlwidget.")
  if (!requireNamespace("htmlwidgets", quietly = TRUE))
    stop("Install approved optional htmlwidgets.")
  if (!is.character(path) || length(path) != 1L || is.na(path) ||
      !grepl("\\.html$", path, ignore.case = TRUE))
    stop("Provide an HTML output path.")
  if (!is.character(data_status) || length(data_status) != 1L ||
      is.na(data_status) || !nzchar(trimws(data_status)))
    stop("Data classification is required.")
  if (!identical(public_release_approved, TRUE) &&
      !identical(public_release_approved, FALSE))
    stop("public_release_approved must be TRUE or FALSE.")
  if (public_release_approved &&
      grepl("PRIVATE|RESTRICTED|PHI", data_status, ignore.case = TRUE))
    stop("Cannot approve public release of private/restricted data.")
  if (!identical(selfcontained, FALSE))
    stop("Use non-self-contained HTML with reviewed local asset dependencies.")
  if (file.exists(path)) stop("Refusing to overwrite HTML.")
  dir.create(dirname(path), recursive = TRUE, showWarnings = FALSE)
  htmlwidgets::saveWidget(widget, file = path, selfcontained = FALSE)
  invisible(path)
}

rt_heatmap_by_condition <- function(x, row_labels, col_labels, condition,
                                    name, unit, condition_levels,
                                    mode = c("sequential", "diverging"),
                                    center = NULL, within_condition = NULL) {
  if (!is.matrix(x) || !is.numeric(x) ||
      ncol(x) != length(col_labels) ||
      length(condition) != ncol(x) ||
      anyNA(condition) || anyNA(col_labels) ||
      anyDuplicated(col_labels))
    stop("Matrix, labels and complete condition vector must align.")
  if (!is.character(condition_levels) || !length(condition_levels) ||
      anyNA(condition_levels) || anyDuplicated(condition_levels) ||
      !setequal(as.character(unique(condition)), condition_levels))
    stop("Declare each observed condition exactly once in desired order.")
  if (!is.null(within_condition) &&
      (length(within_condition) != ncol(x) || anyNA(within_condition)))
    stop("Within-condition sort values must align to samples and be complete.")
  ordering <- order(match(as.character(condition), condition_levels),
                    if (is.null(within_condition)) seq_len(ncol(x)) else within_condition,
                    seq_len(ncol(x)), method = "radix")
  p <- rt_heatmap(x[, ordering, drop = FALSE], row_labels,
                  col_labels[ordering], name, unit,
                  mode = match.arg(mode), center = center)
  p + ggplot2::labs(
    subtitle = paste0(nrow(x), " features x ", ncol(x),
                      " samples | condition order: ",
                      paste(condition_levels, collapse = " > "),
                      " | missing cells=", sum(is.na(x))),
    caption = paste0(p$labels$caption,
      "\\nSamples grouped by declared condition; no clustering or inferred significance.")
  )
}
