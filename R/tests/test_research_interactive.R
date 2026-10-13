# Tests for condition ordering and interactive authorization.
source("R/research_tidy.R")
source("R/research_plots.R")
source("R/research_interactive.R")
if (requireNamespace("ggplot2", quietly = TRUE) &&
    requireNamespace("dplyr", quietly = TRUE) &&
    requireNamespace("tidyr", quietly = TRUE) &&
    requireNamespace("tibble", quietly = TRUE)) {
  m <- matrix(c(2, 1, 4, 3, 6, 5), nrow = 2)
  p <- rt_heatmap_by_condition(
    m, c("Gene A", "Gene B"), c("S_A", "S_B", "S_C"),
    condition = c("Tumor", "Normal", "Tumor"),
    name = "Synthetic measurement", unit = "unitless",
    condition_levels = c("Normal", "Tumor"),
    mode = "diverging", center = 0
  )
  stopifnot(inherits(p, "ggplot"),
            identical(levels(p$data$sample_id),
                      c("S_B", "S_A", "S_C")))
  invalid <- try(rt_heatmap_by_condition(
    m, c("Gene A", "Gene B"), c("S_A", "S_B", "S_C"),
    condition = c("Tumor", "Normal", "Tumor"),
    name = "Synthetic", unit = "unitless",
    condition_levels = c("Tumor")), silent = TRUE)
  stopifnot(inherits(invalid, "try-error"))
  if (requireNamespace("plotly", quietly = TRUE)) {
    widget <- rt_interactive(p)
    stopifnot(inherits(widget, "plotly"))
    if (requireNamespace("htmlwidgets", quietly = TRUE)) {
      denied <- try(rt_save_interactive(
        widget, tempfile(fileext = ".html"),
        data_status = "PRIVATE", public_release_approved = TRUE
      ), silent = TRUE)
      stopifnot(inherits(denied, "try-error"))
    }
  }
}
