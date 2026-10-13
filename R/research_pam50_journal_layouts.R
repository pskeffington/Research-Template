# Read-only publication-layout plans for frozen PAM50 heatmap masters.
# Author: Paul Skeffington. Prepared with OpenAI.
# Journal rules require renewed editorial verification before any submission.
# This module never changes values, renders a figure or selects a journal.

rt_pam50_journal_presets <- function() {
  list(
    J03 = list(journal = "PLOS ONE", width_in = 7.5, height_in = 8.75,
               width_basis = "OFFICIAL_ARTWORK_MAXIMUM",
               height_basis = "OFFICIAL_ARTWORK_MAXIMUM",
               source = "https://journals.plos.org/plosone/s/figures"),
    J04 = list(journal = "PLOS Biology", width_in = 7.5, height_in = 8.75,
               width_basis = "OFFICIAL_ARTWORK_MAXIMUM",
               height_basis = "OFFICIAL_ARTWORK_MAXIMUM",
               source = "https://journals.plos.org/plosbiology/s/figures"),
    J01 = list(journal = "Nature Communications",
               width_in = 180 / 25.4, height_in = 8.75,
               width_basis = "OFFICIAL_DOUBLE_COLUMN_WIDTH_ONLY",
               height_basis = "ENGINEERING_PLANNING_ASSUMPTION",
               source = "https://www.nature.com/ncomms/submit/how-to-submit"),
    J05 = list(journal = "Bioinformatics",
               width_in = 178 / 25.4, height_in = 8.75,
               width_basis = "OFFICIAL_DOUBLE_COLUMN_WIDTH_ONLY",
               height_basis = "ENGINEERING_PLANNING_ASSUMPTION",
               source = "https://academic.oup.com/BIOINFORMATICS/pages/author-guidelines")
  )
}

rt_pam50_journal_layout <- function(paired_meta, contrasts_meta, preset_id) {
  presets <- rt_pam50_journal_presets()
  if (!is.character(preset_id) || length(preset_id) != 1L ||
      is.na(preset_id) || !preset_id %in% names(presets))
    stop("A defined and sourced journal layout scenario must be named.")
  if (!requireNamespace("digest", quietly = TRUE))
    stop("SHA-256 digest is required to bind source gene ordering.")
  if (!is.list(paired_meta) || !is.list(contrasts_meta))
    stop("Require frozen main-panel export metadata for both heatmaps.")
  profile <- c("Basal", "Her2", "LumA", "LumB")
  contrasts <- c("Basal_vs_LumA", "Her2_vs_LumA", "LumB_vs_LumA",
                 "Basal_vs_Her2", "Basal_vs_LumB", "Her2_vs_LumB")
  ids <- paired_meta$gene_order
  labels <- paired_meta$gene_labels
  if (!is.character(ids) || length(ids) != 60L ||
      anyNA(ids) || any(!nzchar(ids)) || anyDuplicated(ids) ||
      !is.character(labels) || length(labels) != 60L ||
      anyNA(labels) || any(!nzchar(labels)) || anyDuplicated(labels))
    stop("Require exactly 60 distinct frozen gene IDs and printable labels.")
  for (meta in list(paired_meta, contrasts_meta)) {
    if (!identical(as.character(meta$gene_order), ids) ||
        !identical(as.character(meta$gene_labels), labels) ||
        !identical(as.character(meta$anchor_order), profile) ||
        !identical(as.character(meta$subtype_order), profile) ||
        !identical(as.character(meta$inferential_status),
                   "POST_SELECTION_DESCRIPTIVE_ONLY") ||
        !identical(meta$sample_level_columns, FALSE) ||
        !identical(as.integer(meta$n_formal_subtype_pairs), 106L) ||
        !identical(as.integer(meta$n_features), 60L) ||
        !identical(meta$scale_policy, "FULL_OBSERVED_RANGE_NO_CLIPPING") ||
        !isTRUE(meta$shared_color_scale) ||
        !identical(as.character(meta$figure_review),
                   "PENDING_VISUAL_AND_SCIENTIFIC_REVIEW") ||
        !identical(as.character(meta$caption_review),
                   "PENDING_AUTHOR_AND_SCIENTIFIC_REVIEW") ||
        !identical(meta$public_release_requested, FALSE))
      stop("Journal planning cannot accept changed identities, inference or review state.")
    if (!identical(unname(as.integer(unlist(meta$anchor_counts[profile]))),
                   rep(15L, 4L)))
      stop("Each frozen anchor block must contain exactly 15 gene rows.")
  }
  if (!identical(as.integer(paired_meta$n_columns), 4L) ||
      !identical(as.integer(contrasts_meta$n_columns), 6L) ||
      !identical(as.character(contrasts_meta$contrast_order), contrasts))
    stop("Require unchanged four subtype effects and six planned contrasts.")
  breaks <- as.numeric(paired_meta$color_breaks)
  if (length(breaks) != 3L || any(!is.finite(breaks)) ||
      breaks[1L] >= 0 || breaks[2L] != 0 ||
      breaks[3L] != -breaks[1L] ||
      !identical(as.numeric(contrasts_meta$color_breaks), breaks))
    stop("Do not replace the full-range shared symmetric color scale.")
  if (!identical(as.numeric(paired_meta$color_center), 0) ||
      !identical(as.numeric(contrasts_meta$color_center), 0))
    stop("All derived pages must retain a zero-centered effect scale.")
  params <- presets[[preset_id]]
  # Deliberately paginate at *complete* 15-gene anchor boundaries.
  # A 30-row figure allows meaningful 9 pt labels without modifying data.
  page_groups <- list(profile[1:2], profile[3:4])
  page_rows <- list(seq_len(30L), 31:60)
  label_pt <- 9
  # Reserved title, names, legend, margins and grouping space in mm.
  reserved_height_mm <- 14 + 13 + 12 + 20 + 25 + 3
  row_pitch_mm <- (params$height_in * 25.4 - reserved_height_mm) / 30
  # The following checks are geometry estimates, not exported PDF QA.
  if (row_pitch_mm * 72 / 25.4 < 1.25 * label_pt)
    stop("Proposed pagination cannot provide a readable 9 pt row-label track.")
  if (params$width_in * 25.4 - 12 < (90 + 40 + 3 + 10))
    stop("Journal planning canvas does not fit matrix, labels and anchor track.")
  pages <- lapply(seq_along(page_rows), function(i) {
    rows <- page_rows[[i]]
    list(
      page = as.integer(i),
      row_start = as.integer(min(rows)),
      row_end = as.integer(max(rows)),
      rows = as.integer(length(rows)),
      anchors = page_groups[[i]],
      genes_per_anchor = 15L,
      first_gene_id = ids[min(rows)],
      last_gene_id = ids[max(rows)],
      gene_order_sha256 = digest::digest(paste(ids[rows], collapse = "\n"),
                                          algo = "sha256", serialize = FALSE),
      label_font_pt = label_pt,
      column_font_pt = 9,
      legend_tick_font_pt = 8.5,
      row_pitch_mm = round(row_pitch_mm, 3)
    )
  })
  # Layout is independent of numeric effect estimates; references both sources.
  list(
    status = "R_LAYOUT_PLAN_ONLY_NOT_RENDERED",
    journal_scenario = preset_id,
    journal_name = params$journal,
    source_url = params$source,
    page_width_in = params$width_in,
    page_height_in = params$height_in,
    width_basis = params$width_basis,
    height_basis = params$height_basis,
    page_count_per_heatmap = 2L,
    heatmap_count = 2L,
    total_review_pages = 4L,
    panels = list(paired_effects = profile, six_contrasts = contrasts),
    pages = pages,
    complete_gene_order_sha256 = digest::digest(
      paste(ids, collapse = "\n"), algo = "sha256", serialize = FALSE),
    shared_color_breaks = breaks,
    shared_color_palette = c("#2166AC", "#F7F7F7", "#B2182B"),
    color_scale = "FULL_OBSERVED_RANGE_NO_CLIPPING",
    anchor_markers = "NAMED_BLOCKS_AND_NONCOLOR_LABELS_REQUIRED",
    captions = "SEPARATE_UNMODIFIED_MANUSCRIPT_CAPTIONS",
    original_master_dimensions_in = c(9, 13),
    original_files_modified = FALSE,
    scientific_estimates_recomputed = FALSE,
    accessibility_review = "HUMAN_PRINT_PROOF_PENDING",
    scientific_review = "PENDING",
    public_release = "BLOCKED"
  )
}
