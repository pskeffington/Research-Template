# Read-only, hash-pinned local import of the frozen R11 research tables.
# Author: Paul Skeffington. Prepared with OpenAI.
# No private paths, frozen hashes or raw data are embedded here; no I/O on source.
rt_read_pam50_locked <- function(st06_file, st07_file, st09_file,
                                 expected_sha256, tolerance = 1e-8) {
  if (!requireNamespace("readr", quietly = TRUE) ||
      !requireNamespace("digest", quietly = TRUE))
    stop("Approved readr and digest dependencies are required.")
  if (any(lengths(list(st06_file, st07_file, st09_file)) != 1L))
    stop("Each frozen source path must be a single file.")
  paths <- stats::setNames(
    c(unname(st06_file), unname(st07_file), unname(st09_file)),
    c("ST06", "ST07", "ST09"))
  if (!is.character(paths) || anyNA(paths) ||
      any(!nzchar(trimws(paths))) || any(!file.exists(paths)) ||
      any(dir.exists(paths)))
    stop("All three approved local frozen CSV files must exist.")
  if (!is.character(expected_sha256) ||
      !identical(names(expected_sha256), names(paths)) ||
      anyNA(expected_sha256) ||
      !all(grepl("^[0-9a-f]{64}$", expected_sha256)))
    stop("Explicit named lowercase SHA-256 pins ST06, ST07, ST09 are required.")
  if (!is.numeric(tolerance) || length(tolerance) != 1L ||
      !is.finite(tolerance) || tolerance <= 0 || tolerance > 1e-6)
    stop("Supply an explicit positive numerical alignment tolerance <=1e-6.")
  hashes <- vapply(paths, digest::digest, character(1),
                   algo = "sha256", file = TRUE)
  if (!identical(unname(hashes), unname(expected_sha256)))
    stop("Frozen source hash mismatch: do not construct research figures.")
  st06 <- readr::read_csv(paths[["ST06"]], show_col_types = FALSE,
                          progress = FALSE)
  st07 <- readr::read_csv(paths[["ST07"]], show_col_types = FALSE,
                          progress = FALSE)
  st09 <- readr::read_csv(paths[["ST09"]], show_col_types = FALSE,
                          progress = FALSE)
  profile <- rt_pam50_profile()
  subtypes <- profile$subtype_order
  effects <- paste0("logFC_", subtypes)
  if (nrow(st06) != 21432L || nrow(st07) != 128592L ||
      nrow(st09) != 60L || !all(c("gene_id", effects) %in% names(st06)) ||
      !all(c("gene_id", "contrast", "first_subtype",
             "second_subtype", "logFC") %in% names(st07)) ||
      !all(c("gene_id", effects, "anchor_subtype", "anchor_rank",
             "selected_signature", "SYMBOL") %in% names(st09)))
    stop("Frozen R11 row counts or columns disagree with ST06/ST07/ST09 contract.")
  if (!is.character(st06$gene_id) || anyNA(st06$gene_id) ||
      anyDuplicated(st06$gene_id) ||
      !is.character(st07$gene_id) || anyNA(st07$gene_id) ||
      !is.character(st07$contrast) || anyNA(st07$contrast) ||
      !setequal(unique(st07$contrast), profile$contrasts) ||
      !all(vapply(st06[effects], is.numeric, logical(1))) ||
      any(!is.finite(as.matrix(st06[effects]))))
    stop("Full frozen gene universe, subtype columns or identifiers are invalid.")
  expected_keys <- paste(st07$gene_id, st07$contrast, sep = "\r")
  if (anyDuplicated(expected_keys) ||
      !setequal(unique(st07$gene_id), st06$gene_id) ||
      !identical(unname(as.integer(table(factor(
        st07$contrast, levels = profile$contrasts)))), rep(21432L, 6L)) ||
      !is.numeric(st07$logFC) || any(!is.finite(st07$logFC)))
    stop("The complete ST07 six-contrast testing universe is incomplete or duplicated.")
  for (contrast in profile$contrasts) {
    spec <- strsplit(contrast, "_vs_", fixed = TRUE)[[1L]]
    index <- which(st07$contrast == contrast)
    if (anyNA(st07$first_subtype[index]) ||
        anyNA(st07$second_subtype[index]) ||
        any(st07$first_subtype[index] != spec[1L]) ||
        any(st07$second_subtype[index] != spec[2L]))
      stop("Frozen ST07 source first-minus-second subtype labels are invalid.")
  }
  if (!is.character(st09$gene_id) || anyNA(st09$gene_id) ||
      !all(st09$gene_id %in% st06$gene_id))
    stop("Frozen ST09 gene IDs are not contained in the full tested universe.")
  loc <- match(st09$gene_id, st06$gene_id)
  for (field in effects) {
    if (!is.numeric(st09[[field]]) ||
        any(!is.finite(st09[[field]])) ||
        max(abs(st09[[field]] - st06[[field]][loc])) > tolerance)
      stop("Frozen selected-gene ST09 effects disagree with ST06.")
  }
  selected <- st07[st07$gene_id %in% st09$gene_id, , drop = FALSE]
  prepared <- rt_prepare_pam50_research(st09, selected, tolerance)
  list(
    signature = st09, selected_contrasts = selected,
    prepared = prepared, source_sha256 = hashes,
    source_path = normalizePath(paths),
    status = "HASH_MATCHED_FROZEN_DESCRIPTIVE_INPUTS",
    inference = "POST_SELECTION_DESCRIPTIVE_ONLY",
    source_reliability = "Matches operator-supplied pins; independent provenance review still required."
  )
}
