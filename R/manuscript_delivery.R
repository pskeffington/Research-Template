# Manuscript-grade figure delivery, explicit opt-in I/O.
# Author: Paul Skeffington. Prepared with OpenAI.
# Source R/research_tidy.R and R/research_plots.R first.
# No I/O occurs on source.
rt_manuscript_export <- function(plot, output_stem, figure_id, legend,
                                 study, data_status, analysis_unit,
                                 source, n_analyzed, n_missing,
                                 inference = "DESCRIPTIVE_ONLY",
                                 dpi = 600L, width = 7, height = 5,
                                 allow_public = FALSE) {
  rt_require()
  if (!inherits(plot, "ggplot")) stop("A ggplot object is required.")
  fields <- list(output_stem = output_stem, figure_id = figure_id,
                 legend = legend, study = study, data_status = data_status,
                 analysis_unit = analysis_unit, source = source,
                 inference = inference)
  if (any(vapply(fields, function(z) !is.character(z) || length(z) != 1L ||
                 is.na(z) || !nzchar(trimws(z)), logical(1)))) {
    stop("All manuscript metadata fields must be nonempty scalar text.")
  }
  if (!grepl("^[A-Za-z0-9_.-]+$", figure_id)) stop("Unsafe figure ID.")
  if (!is.numeric(n_analyzed) || length(n_analyzed) != 1L ||
      !is.finite(n_analyzed) || n_analyzed < 1 || n_analyzed != floor(n_analyzed) ||
      !is.numeric(n_missing) || length(n_missing) != 1L ||
      !is.finite(n_missing) || n_missing < 0 || n_missing != floor(n_missing))
    stop("Denominators must be nonnegative whole numbers, analyzed n > 0.")
  if (!is.numeric(dpi) || length(dpi) != 1L || !is.finite(dpi) || dpi < 300 ||
      !is.numeric(width) || length(width) != 1L || !is.finite(width) || width <= 0 ||
      !is.numeric(height) || length(height) != 1L || !is.finite(height) || height <= 0)
    stop("Need >=300 dpi and positive finite dimensions.")
  if (grepl("INFERENTIAL|P_VALUE|FDR|CI", inference, ignore.case = TRUE) &&
      !grepl("VERIFIED", inference, fixed = TRUE))
    stop("Inferential delivery requires an explicitly VERIFIED inference state.")
  if (grepl("PRIVATE|RESTRICTED|PHI", data_status, ignore.case = TRUE) && allow_public)
    stop("Restricted or private data cannot be marked public.")
  if (grepl("[\\\\/]$", output_stem) || !nzchar(basename(output_stem)))
    stop("A basename is required.")
  paths <- paste0(output_stem, c(".pdf", ".png"))
  if (any(file.exists(paths))) stop("Refusing to overwrite an existing figure.")
  dir.create(dirname(output_stem), recursive = TRUE, showWarnings = FALSE)
  metadata <- list(
    figure_id = figure_id, study = study, legend = legend,
    analysis_unit = analysis_unit, source = source, data_status = data_status,
    n_analyzed = as.integer(n_analyzed), n_missing = as.integer(n_missing),
    inference = inference, dpi = dpi, width_in = width, height_in = height,
    public_release_approved = isTRUE(allow_public),
    figure_review = "PENDING_VISUAL_AND_SCIENTIFIC_REVIEW"
  )
  # Cairo PDF, when installed, ensures vector text and vector geometry.
  # Otherwise use the default PDF device; inspect font embedding separately.
  pdf_device <- if (capabilities("cairo")) grDevices::cairo_pdf else "pdf"
  ggplot2::ggsave(paths[[1]], plot = plot, device = pdf_device,
                  width = width, height = height, units = "in", bg = "white")
  ggplot2::ggsave(paths[[2]], plot = plot, dpi = dpi,
                  width = width, height = height, units = "in", bg = "white")
  metadata$files <- paths
  metadata$sha256 <- if (requireNamespace("digest", quietly = TRUE)) {
    vapply(paths, digest::digest, character(1), algo = "sha256", file = TRUE)
  } else {
    NULL
  }
  # Structured sidecar is human-readable; JSON is optional via jsonlite.
  sidecar <- paste0(output_stem, ".metadata.rds")
  if (file.exists(sidecar)) stop("Refusing to overwrite metadata.")
  saveRDS(metadata, sidecar)
  if (requireNamespace("jsonlite", quietly = TRUE)) {
    json_path <- paste0(output_stem, ".metadata.json")
    if (file.exists(json_path)) stop("Refusing to overwrite metadata JSON.")
    jsonlite::write_json(metadata, json_path, auto_unbox = TRUE, pretty = TRUE)
  }
  invisible(metadata)
}
