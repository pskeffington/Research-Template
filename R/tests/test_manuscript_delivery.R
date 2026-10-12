# Manuscript export smoke and invalid-state rejection on synthetic data.
source("R/research_tidy.R")
source("R/research_plots.R")
source("R/manuscript_delivery.R")
source("R/synthetic_demo.R")
if (requireNamespace("ggplot2", quietly = TRUE) &&
    requireNamespace("dplyr", quietly = TRUE) &&
    requireNamespace("tidyr", quietly = TRUE) &&
    requireNamespace("tibble", quietly = TRUE)) {
  x <- make_synthetic_cohort(n = 90L, seed = 711L)
  p <- rt_violin(x, "site", "measurement_mg_dl",
                 "Synthetic measurement", "mg/dL",
                 levels = c("North", "South", "West"))
  stopifnot(inherits(p, "ggplot"), length(p$layers) >= 2L)
  err <- try(rt_manuscript_export(
    p, tempfile("bad"), "Figure_01", "Synthetic", "Study",
    "PRIVATE", "person", "synthetic", 90L, 0L,
    allow_public = TRUE), silent = TRUE)
  stopifnot(inherits(err, "try-error"))
  stem <- tempfile("figure_")
  result <- rt_manuscript_export(
    p, stem, "Figure_01", "Synthetic distribution", "Study",
    "SYNTHETIC", "person", "synthetic seed 711", 90L, 0L)
  stopifnot(all(file.exists(result$files)),
            file.exists(paste0(stem, ".metadata.rds")),
            identical(result$figure_review,
                      "PENDING_VISUAL_AND_SCIENTIFIC_REVIEW"))
  unlink(c(result$files, paste0(stem, ".metadata.rds"),
           paste0(stem, ".metadata.json")))
}
