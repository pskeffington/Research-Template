# Base-contract tests run even without optional Bioconductor plotting packages.
source("R/research_tidy.R")
source("R/research_plots.R")
source("R/research_complex_heatmap.R")
values <- matrix(c(-1, 2, NA, 4, 3, -3), nrow = 2,
                 dimnames = list(c("G1", "G2"), c("T1", "N1", "T2")))
meta <- data.frame(sample_id = c("T2", "T1", "N1"),
                   condition = c("Tumor", "Tumor", "Normal"),
                   subtype = c("LumA", "Basal", NA_character_),
                   stringsAsFactors = FALSE)
prepared <- rt_prepare_complex_heatmap(
  values, meta, condition_levels = c("Normal", "Tumor"),
  annotations = "subtype")
stopifnot(identical(prepared$sample_order, c("N1", "T1", "T2")),
          identical(colnames(prepared$values), c("N1", "T1", "T2")),
          prepared$n_missing == 1L,
          identical(unname(prepared$condition_counts), c(1L, 2L)),
          identical(as.character(prepared$sample_metadata$subtype),
                    c(NA_character_, "Basal", "LumA")))
invalid_meta <- meta[-1, ]
stopifnot(inherits(try(rt_prepare_complex_heatmap(
  values, invalid_meta, condition_levels = c("Normal", "Tumor")),
  silent = TRUE), "try-error"))
stopifnot(inherits(try(rt_prepare_complex_heatmap(
  values, meta, condition_levels = c("Tumor")),
  silent = TRUE), "try-error"))
bad <- values
colnames(bad)[3] <- "N1"
stopifnot(inherits(try(rt_prepare_complex_heatmap(
  bad, meta, condition_levels = c("Normal", "Tumor")),
  silent = TRUE), "try-error"))
bad <- values
bad[1, 2] <- Inf
stopifnot(inherits(try(rt_prepare_complex_heatmap(
  bad, meta, condition_levels = c("Normal", "Tumor")),
  silent = TRUE), "try-error"))

if (requireNamespace("ComplexHeatmap", quietly = TRUE) &&
    requireNamespace("circlize", quietly = TRUE)) {
  heatmap <- rt_complex_heatmap(
    values, meta, condition_levels = c("Normal", "Tumor"),
    measurement = "Synthetic effect", unit = "log2 units",
    value_transform = "No additional transformation",
    mode = "diverging", center = 0, annotations = "subtype")
  stopifnot(inherits(heatmap, "rt_complex_heatmap"),
            inherits(heatmap$heatmap, "Heatmap"),
            !heatmap$rasterize,
            identical(heatmap$prepared$sample_order, c("N1", "T1", "T2")))
  bad_center <- try(rt_complex_heatmap(
    values, meta, condition_levels = c("Normal", "Tumor"),
    measurement = "Effect", unit = "log2 units",
    value_transform = "none", mode = "diverging"),
    silent = TRUE)
  stopifnot(inherits(bad_center, "try-error"))
  stem <- tempfile("complex_heatmap_")
  deliver <- rt_export_complex_heatmap(
    heatmap, stem, figure_id = "SyntheticFigure",
    legend = "Synthetic conditions, with missing data",
    source = "Fully synthetic matrix",
    data_status = "SYNTHETIC", width = 4, height = 3, dpi = 300)
  files <- paste0(stem, c(".pdf", ".png", ".metadata.rds"))
  stopifnot(all(file.exists(files)), all(file.info(files)$size > 0),
            identical(deliver$figure_review, "PENDING_VISUAL_AND_SCIENTIFIC_REVIEW"),
            identical(deliver$sample_order, c("N1", "T1", "T2")))
  rejected <- try(rt_export_complex_heatmap(
    heatmap, tempfile("blocked_"), "Synthetic", "Synthetic",
    "Synthetic source", "PRIVATE", public_release_approved = TRUE), silent = TRUE)
  stopifnot(inherits(rejected, "try-error"))
  unlink(files)
}
cat("ComplexHeatmap preparation, guards, and optional renderer PASS\\n")
