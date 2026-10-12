# Automated structural figure QA. This is not scientific or visual approval.
# Author: Paul Skeffington. Prepared with OpenAI.
# Source defines functions only; audit requires png + Poppler utilities.
rt_figure_audit <- function(output_stem, min_ink_fraction = 0.0001,
                            require_embedded_fonts = TRUE) {
  if (!is.character(output_stem) || length(output_stem) != 1L ||
      is.na(output_stem) || !nzchar(trimws(output_stem)))
    stop("An output stem is required.")
  if (!is.numeric(min_ink_fraction) || length(min_ink_fraction) != 1L ||
      !is.finite(min_ink_fraction) ||
      min_ink_fraction <= 0 || min_ink_fraction >= 1)
    stop("Choose a fractional non-white pixel threshold between zero and one.")
  if (!is.logical(require_embedded_fonts) ||
      length(require_embedded_fonts) != 1L || is.na(require_embedded_fonts))
    stop("Font embedding check must be TRUE or FALSE.")
  if (!requireNamespace("png", quietly = TRUE))
    stop("The optional png package is required for automated figure QA.")
  if (!nzchar(Sys.which("pdfinfo")) || !nzchar(Sys.which("pdffonts")))
    stop("Install Poppler pdfinfo and pdffonts for figure audit.")
  paths <- stats::setNames(paste0(output_stem,
                                   c(".pdf", ".png", ".metadata.rds")),
                           c("pdf", "png", "metadata"))
  if (!all(file.exists(paths)) || any(file.info(paths)$size <= 0))
    stop("PDF, PNG and RDS provenance files must exist and be nonempty.")
  meta <- readRDS(paths[["metadata"]])
  if (!identical(meta$figure_review, "PENDING_VISUAL_AND_SCIENTIFIC_REVIEW"))
    stop("Figure must remain pending scientific and visual review.")
  required <- c("figure_id", "legend", "source", "data_status",
                "width_in", "height_in", "dpi", "files")
  if (!all(required %in% names(meta)) ||
      any(!nzchar(c(meta$figure_id, meta$legend, meta$source,
                    meta$data_status))))
    stop("Incomplete figure provenance metadata.")
  if (!is.numeric(meta$width_in) || !is.numeric(meta$height_in) ||
      !is.numeric(meta$dpi) || length(meta$dpi) != 1L ||
      any(!is.finite(c(meta$width_in, meta$height_in, meta$dpi))) ||
      any(c(meta$width_in, meta$height_in) <= 0) || meta$dpi < 300)
    stop("Requested dimensions and resolution must be documented.")
  if (!identical(normalizePath(as.character(meta$files)),
                 normalizePath(paths[c("pdf", "png")])))
    stop("Provenance must identify the matching figure files.")
  if ("sha256" %in% names(meta) && length(meta$sha256)) {
    if (!requireNamespace("digest", quietly = TRUE))
      stop("The digest package is required to verify recorded checksums.")
    calculated <- vapply(paths[c("pdf", "png")], digest::digest, character(1),
                         file = TRUE, algo = "sha256")
    if (!identical(unname(calculated), unname(as.character(meta$sha256))))
      stop("Figure checksums do not match provenance.")
  }
  image <- png::readPNG(paths[["png"]], info = TRUE)
  shape <- dim(image)
  if (length(shape) < 2L)
    stop("PNG image has no decodable dimensions.")
  expected <- round(c(meta$height_in, meta$width_in) * meta$dpi)
  if (any(abs(shape[1:2] - expected) > 2))
    stop("PNG pixel dimensions disagree with declared inches/dpi.")
  if (length(shape) == 2L) {
    ink <- mean(image < 0.97)
  } else {
    channels <- seq_len(min(3L, shape[3]))
    ink_mask <- image[, , channels[1]] < 0.97
    if (length(channels) > 1L) {
      for (channel in channels[-1L])
        ink_mask <- ink_mask | image[, , channel] < 0.97
    }
    ink <- mean(ink_mask)
  }
  if (!is.finite(ink) || ink < min_ink_fraction)
    stop("PNG has insufficient visible content and may be blank.")
  run_poppler <- function(program, arguments) {
    report <- suppressWarnings(system2(program, args = arguments,
                                       stdout = TRUE, stderr = TRUE))
    if (!is.null(attr(report, "status")) && attr(report, "status") != 0L)
      stop(sprintf("%s failed while inspecting manuscript figure.", program))
    report
  }
  pdf_report <- run_poppler("pdfinfo",
                            c("-box", shQuote(paths[["pdf"]])))
  n_pages <- grep("^Pages:", pdf_report, value = TRUE)
  if (length(n_pages) != 1L ||
      !identical(as.integer(trimws(sub("^Pages:", "", n_pages))), 1L))
    stop("Manuscript PDF must contain exactly one page.")
  page_size <- grep("^Page size:", pdf_report, value = TRUE)
  match <- regmatches(page_size,
    regexec("Page size:[[:space:]]*([0-9.]+)[[:space:]]*x[[:space:]]*([0-9.]+)[[:space:]]*pts",
            page_size))
  if (length(match) != 1L || length(match[[1]]) != 3L)
    stop("Cannot determine PDF page dimensions.")
  dimensions_pt <- as.numeric(match[[1]][2:3])
  if (any(abs(dimensions_pt - 72 * c(meta$width_in, meta$height_in)) > 1))
    stop("PDF dimensions disagree with declared manuscript size.")
  font_report <- run_poppler("pdffonts", shQuote(paths[["pdf"]]))
  font_rows <- if (length(font_report) > 2L) font_report[-c(1L, 2L)] else character()
  has_fonts <- length(font_rows) > 0L
  all_embedded <- has_fonts &&
    !any(grepl("[[:space:]]no[[:space:]]", font_rows))
  if (require_embedded_fonts && !all_embedded)
    stop("PDF font embedding could not be established for all fonts.")
  if (!is.null(meta$n_samples)) {
    if (length(meta$sample_order) != meta$n_samples ||
        anyDuplicated(meta$sample_order))
      stop("Heatmap sample order violates declared sample count.")
    if (sum(as.integer(meta$condition_counts)) != meta$n_samples)
      stop("Heatmap condition counts do not sum to sample count.")
  }
  report <- list(
    figure_id = meta$figure_id, pdf_pages = 1L,
    png_pixels = stats::setNames(as.integer(shape[1:2]), c("height", "width")),
    dimensions_in = c(width = meta$width_in, height = meta$height_in),
    nominal_dpi = meta$dpi, nonwhite_fraction = ink,
    fonts_embedded = all_embedded, checksum_checked = length(meta$sha256) > 0L,
    automated_checks = "PASS",
    scientific_review = "PENDING",
    visual_review = "PENDING"
  )
  invisible(report)
}
