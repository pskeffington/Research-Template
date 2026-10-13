# Synthetic-only journal planning tests; preserve frozen source metadata.
# Author: Paul Skeffington. Prepared with OpenAI.
source("R/research_pam50_journal_layouts.R")

ids <- sprintf("SYN_G%03d", seq_len(60L))
labels <- paste0("Synthetic_", seq_len(60L))
profile <- c("Basal", "Her2", "LumA", "LumB")
pairs <- c("Basal_vs_LumA", "Her2_vs_LumA", "LumB_vs_LumA",
           "Basal_vs_Her2", "Basal_vs_LumB", "Her2_vs_LumB")
make_meta <- function(kind) {
  list(
    gene_order = ids, gene_labels = labels,
    anchor_order = profile, subtype_order = profile,
    anchor_counts = as.list(stats::setNames(rep(15L, 4L), profile)),
    inferential_status = "POST_SELECTION_DESCRIPTIVE_ONLY",
    sample_level_columns = FALSE, n_formal_subtype_pairs = 106L,
    n_features = 60L, n_columns = if (kind == "paired") 4L else 6L,
    contrast_order = if (kind == "paired") NULL else pairs,
    scale_policy = "FULL_OBSERVED_RANGE_NO_CLIPPING",
    shared_color_scale = TRUE,
    figure_review = "PENDING_VISUAL_AND_SCIENTIFIC_REVIEW",
    caption_review = "PENDING_AUTHOR_AND_SCIENTIFIC_REVIEW",
    public_release_requested = FALSE, color_center = 0,
    color_breaks = c(-8, 0, 8)
  )
}
paired <- make_meta("paired")
contrast <- make_meta("contrast")
original_paired <- unserialize(serialize(paired, NULL))
original_contrast <- unserialize(serialize(contrast, NULL))
presets <- rt_pam50_journal_presets()
stopifnot(identical(names(presets), c("J03", "J04", "J01", "J05")))

for (key in names(presets)) {
  plan <- rt_pam50_journal_layout(paired, contrast, key)
  stopifnot(identical(plan$status, "R_LAYOUT_PLAN_ONLY_NOT_RENDERED"),
            identical(plan$journal_scenario, key),
            identical(plan$shared_color_breaks, c(-8, 0, 8)),
            identical(plan$shared_color_palette,
                      c("#2166AC", "#F7F7F7", "#B2182B")),
            identical(plan$color_scale, "FULL_OBSERVED_RANGE_NO_CLIPPING"),
            identical(plan$page_count_per_heatmap, 2L),
            identical(plan$total_review_pages, 4L),
            identical(plan$panels$paired_effects, profile),
            identical(plan$panels$six_contrasts, pairs),
            identical(vapply(plan$pages, function(z) z$row_start, integer(1)),
                      c(1L, 31L)),
            identical(vapply(plan$pages, function(z) z$row_end, integer(1)),
                      c(30L, 60L)),
            identical(plan$pages[[1]]$anchors, c("Basal", "Her2")),
            identical(plan$pages[[2]]$anchors, c("LumA", "LumB")),
            all(vapply(plan$pages, function(z)
              z$row_pitch_mm > 3.97 && z$label_font_pt >= 9 &&
                z$legend_tick_font_pt >= 8 && z$genes_per_anchor == 15L,
              logical(1))),
            identical(plan$scientific_estimates_recomputed, FALSE),
            identical(plan$original_files_modified, FALSE),
            identical(plan$public_release, "BLOCKED"),
            identical(plan$accessibility_review, "HUMAN_PRINT_PROOF_PENDING"))
  if (key %in% c("J01", "J05"))
    stopifnot(identical(plan$height_basis,
                        "ENGINEERING_PLANNING_ASSUMPTION"))
  else
    stopifnot(identical(plan$height_basis,
                        "OFFICIAL_ARTWORK_MAXIMUM"))
}
stopifnot(identical(paired, original_paired),
          identical(contrast, original_contrast))
expect_block <- function(expression) {
  if (!inherits(try(expression, silent = TRUE), "try-error"))
    stop("Corrupted manuscript metadata unexpectedly passed journal planning.")
}
expect_block(rt_pam50_journal_layout(paired, contrast, "J09"))
bad <- contrast
bad$gene_order <- rev(ids)
expect_block(rt_pam50_journal_layout(paired, bad, "J03"))
bad <- paired
bad$gene_labels[2L] <- bad$gene_labels[1L]
expect_block(rt_pam50_journal_layout(bad, contrast, "J03"))
bad <- contrast
bad$color_breaks <- c(-7, 0, 8)
expect_block(rt_pam50_journal_layout(paired, bad, "J03"))
bad <- paired
bad$shared_color_scale <- FALSE
expect_block(rt_pam50_journal_layout(bad, contrast, "J03"))
bad <- contrast
bad$contrast_order <- rev(pairs)
expect_block(rt_pam50_journal_layout(paired, bad, "J03"))
bad <- paired
bad$figure_review <- "APPROVED"
expect_block(rt_pam50_journal_layout(bad, contrast, "J03"))
bad <- contrast
bad$anchor_counts$LumB <- 14L
expect_block(rt_pam50_journal_layout(paired, bad, "J03"))
bad <- paired
bad$n_formal_subtype_pairs <- 109L
expect_block(rt_pam50_journal_layout(bad, contrast, "J03"))
bad <- contrast
bad$sample_level_columns <- TRUE
expect_block(rt_pam50_journal_layout(paired, bad, "J03"))
cat("PAM50 journal R-layout planning PASS: 4 scenarios, intact 60-gene frozen blocks and shared scale\n")
