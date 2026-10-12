# Explicit failure-path checks for the manuscript artifact integrity gate.
# Author: Paul Skeffington. Prepared with OpenAI.
source("R/research_figure_audit.R")
stopifnot(requireNamespace("png", quietly = TRUE),
          requireNamespace("digest", quietly = TRUE))

root <- "artifacts/ci_figure_review"
suffixes <- c(".pdf", ".png", ".metadata.rds")
stage <- function(name = "violin_with_box") {
  origin <- file.path(root, name)
  directory <- tempfile("figure_audit_negative_")
  dir.create(directory, recursive = TRUE)
  stem <- file.path(directory, name)
  stopifnot(all(file.copy(paste0(origin, suffixes),
                             paste0(stem, suffixes))))
  meta <- readRDS(paste0(stem, ".metadata.rds"))
  meta$files <- paste0(stem, c(".pdf", ".png"))
  saveRDS(meta, paste0(stem, ".metadata.rds"))
  stem
}
refresh_hashes <- function(stem) {
  meta_path <- paste0(stem, ".metadata.rds")
  meta <- readRDS(meta_path)
  meta$sha256 <- vapply(meta$files, digest::digest, character(1),
                        file = TRUE, algo = "sha256")
  saveRDS(meta, meta_path)
}
expect_rejected <- function(stem, reason) {
  result <- try(rt_figure_audit(stem), silent = TRUE)
  if (!inherits(result, "try-error"))
    stop(sprintf("Corrupted figure incorrectly admitted: %s", reason))
  cat(sprintf("Rejected: %s\n", reason))
}
valid <- stage()
refresh_hashes(valid)
stopifnot(identical(rt_figure_audit(valid)$automated_checks, "PASS"))

missing_png <- stage()
unlink(paste0(missing_png, ".png"))
expect_rejected(missing_png, "missing PNG")

missing_metadata <- stage()
unlink(paste0(missing_metadata, ".metadata.rds"))
expect_rejected(missing_metadata, "missing provenance")

tampered_hash <- stage()
refresh_hashes(tampered_hash)
meta <- readRDS(paste0(tampered_hash, ".metadata.rds"))
meta$sha256[1] <- paste(rep("0", 64L), collapse = "")
saveRDS(meta, paste0(tampered_hash, ".metadata.rds"))
expect_rejected(tampered_hash, "checksum mismatch")

missing_hash <- stage()
meta <- readRDS(paste0(missing_hash, ".metadata.rds"))
meta$sha256 <- NULL
saveRDS(meta, paste0(missing_hash, ".metadata.rds"))
expect_rejected(missing_hash, "missing checksum")

corrupt_png <- stage()
writeBin(as.raw(c(0L, 17L, 31L, 63L)), paste0(corrupt_png, ".png"))
refresh_hashes(corrupt_png)
expect_rejected(corrupt_png, "corrupted PNG bytes")

corrupt_pdf <- stage()
writeBin(as.raw(c(0L, 17L, 31L, 63L)), paste0(corrupt_pdf, ".pdf"))
refresh_hashes(corrupt_pdf)
expect_rejected(corrupt_pdf, "corrupted PDF bytes")

wrong_pixels <- stage()
png::writePNG(array(0.5, dim = c(30L, 30L, 3L)),
              paste0(wrong_pixels, ".png"))
refresh_hashes(wrong_pixels)
expect_rejected(wrong_pixels, "incorrect pixel dimensions")

blank_png <- stage()
image <- png::readPNG(paste0(blank_png, ".png"))
image[] <- 1
png::writePNG(image, paste0(blank_png, ".png"))
refresh_hashes(blank_png)
expect_rejected(blank_png, "entirely blank PNG with valid resolution")

wrong_page <- stage()
grDevices::pdf(paste0(wrong_page, ".pdf"), width = 6, height = 4)
graphics::plot.new()
graphics::text(0.5, 0.5, labels = "Synthetic mismatched page")
grDevices::dev.off()
refresh_hashes(wrong_page)
expect_rejected(wrong_page, "PDF page dimensions disagree with metadata")

unembedded <- stage()
grDevices::pdf(paste0(unembedded, ".pdf"), width = 7, height = 5,
               family = "Helvetica")
graphics::plot.new()
graphics::text(0.5, 0.5, labels = "Unembedded base PDF font")
grDevices::dev.off()
refresh_hashes(unembedded)
expect_rejected(unembedded, "PDF contains unembedded font")

mismatched_metadata <- stage("condition_heatmap")
refresh_hashes(mismatched_metadata)
meta <- readRDS(paste0(mismatched_metadata, ".metadata.rds"))
meta$n_samples <- meta$n_samples + 1L
saveRDS(meta, paste0(mismatched_metadata, ".metadata.rds"))
expect_rejected(mismatched_metadata, "sample count disagrees with sample order")

restricted_public <- stage()
refresh_hashes(restricted_public)
meta <- readRDS(paste0(restricted_public, ".metadata.rds"))
meta$data_status <- "RESTRICTED"
meta$public_release_approved <- TRUE
saveRDS(meta, paste0(restricted_public, ".metadata.rds"))
expect_rejected(restricted_public, "restricted data incorrectly marked public")

released <- stage()
refresh_hashes(released)
meta <- readRDS(paste0(released, ".metadata.rds"))
meta$figure_review <- "APPROVED"
saveRDS(meta, paste0(released, ".metadata.rds"))
expect_rejected(released, "manually overridden review status")

cat("Figure audit negative tests PASS: clean fixture accepted; 13 corrupt or unsafe variants rejected\n")
