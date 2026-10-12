# Frozen PAM50 schema alignment: entirely synthetic, without protected gene names.
source("R/research_tidy.R")
source("R/research_plots.R")
source("R/research_pam50_heatmaps.R")
source("R/research_pam50_scale_diagnostic.R")
source("R/manuscript_delivery.R")
source("R/research_figure_audit.R")

profile <- rt_pam50_profile()
subtypes <- profile$subtype_order
stopifnot(identical(subtypes, c("Basal", "Her2", "LumA", "LumB")),
          identical(unname(profile$n_pairs), c(16L, 9L, 59L, 22L)),
          sum(profile$n_pairs) == 106L, length(profile$contrasts) == 6L)
set.seed(711)
genes <- sprintf("SYN_G%03d", seq_len(60L))
anchors <- rep(subtypes, each = 15L)
signature <- data.frame(
  gene_id = genes, SYMBOL = paste0("Synthetic_", seq_len(60L)),
  anchor_subtype = anchors, anchor_rank = rep(seq_len(15L), 4L),
  selected_signature = TRUE, stringsAsFactors = FALSE
)
values <- matrix(stats::rnorm(240L), nrow = 60L, ncol = 4L)
for (s in seq_along(subtypes))
  values[anchors == subtypes[s], s] <-
    values[anchors == subtypes[s], s] + 8.0
for (s in seq_along(subtypes))
  signature[[paste0("logFC_", subtypes[s])]] <- values[, s]
pairs <- strsplit(profile$contrasts, "_vs_", fixed = TRUE)
contrasts <- do.call(rbind, lapply(seq_along(profile$contrasts), function(i) {
  first <- pairs[[i]][1L]
  second <- pairs[[i]][2L]
  data.frame(gene_id = genes, contrast = profile$contrasts[i],
             first_subtype = first, second_subtype = second,
             logFC = signature[[paste0("logFC_", first)]] -
                     signature[[paste0("logFC_", second)]],
             stringsAsFactors = FALSE)
}))
# Intentional unsorted input to ensure ID/anchor/rank alignment, not file row order.
signature <- signature[sample(seq_len(60L)), , drop = FALSE]
contrasts <- contrasts[sample(seq_len(360L)), , drop = FALSE]
prepared <- rt_prepare_pam50_research(signature, contrasts)
stopifnot(identical(prepared$gene_id, genes),
          identical(dim(prepared$effects), c(60L, 4L)),
          identical(dim(prepared$contrasts), c(60L, 6L)),
          identical(levels(prepared$anchor), subtypes),
          identical(colnames(prepared$effects), subtypes),
          identical(colnames(prepared$contrasts), profile$contrasts),
          identical(prepared$matrix_semantics, "gene_by_modeled_effect"),
          identical(prepared$sample_level_columns, FALSE))
# Every planned contrast must remain exactly first - second.
for (j in seq_along(profile$contrasts)) {
  pair <- pairs[[j]]
  stopifnot(max(abs(prepared$contrasts[, j] -
                    (prepared$effects[, pair[1L]] -
                     prepared$effects[, pair[2L]]))) < 1e-12)
}
expect_failure <- function(expr) {
  if (!inherits(try(expr, silent = TRUE), "try-error"))
    stop("Research-alignment contract admitted corrupted input.")
}
bad <- signature[-1, ]
expect_failure(rt_prepare_pam50_research(bad, contrasts))
bad <- signature
bad$gene_id[1L] <- bad$gene_id[2L]
expect_failure(rt_prepare_pam50_research(bad, contrasts))
bad <- signature
bad$anchor_rank[1L] <- bad$anchor_rank[2L]
expect_failure(rt_prepare_pam50_research(bad, contrasts))
bad <- signature
bad$anchor_subtype[1L] <- subtypes[which(subtypes != bad$anchor_subtype[1L])[1L]]
expect_failure(rt_prepare_pam50_research(bad, contrasts))
bad <- signature
bad$selected_signature[1L] <- FALSE
expect_failure(rt_prepare_pam50_research(bad, contrasts))
# Swapping two rank-1 anchors preserves all 15-per-anchor counts and ranks,
# so only the highest-effect anchor semantic gate can reject it.
bad <- signature
a <- which(bad$anchor_subtype == "Basal" & bad$anchor_rank == 1L)
b <- which(bad$anchor_subtype == "Her2" & bad$anchor_rank == 1L)
bad$anchor_subtype[c(a, b)] <- bad$anchor_subtype[c(b, a)]
expect_failure(rt_prepare_pam50_research(bad, contrasts))
bad <- contrasts[-1, ]
expect_failure(rt_prepare_pam50_research(signature, bad))
bad <- contrasts
bad$logFC[1L] <- bad$logFC[1L] + 0.01
expect_failure(rt_prepare_pam50_research(signature, bad))
bad <- contrasts
bad$first_subtype[1L] <- subtypes[which(subtypes != bad$first_subtype[1L])[1L]]
expect_failure(rt_prepare_pam50_research(signature, bad))
bad <- signature
bad$SYMBOL[c(1L, 2L)] <- "DuplicateLabel"
dedup <- rt_prepare_pam50_research(bad, contrasts)
symbol_rows <- match(bad$gene_id[c(1L, 2L)], dedup$gene_id)
stopifnot(!anyDuplicated(dedup$gene_labels), !anyNA(symbol_rows),
          all(grepl("DuplicateLabel",
                    dedup$gene_labels[symbol_rows], fixed = TRUE)))

stopifnot(requireNamespace("ComplexHeatmap", quietly = TRUE),
          requireNamespace("circlize", quietly = TRUE),
          requireNamespace("digest", quietly = TRUE),
          requireNamespace("jsonlite", quietly = TRUE))
bundle <- rt_pam50_research_heatmaps(signature, contrasts)
previous_gap <- ComplexHeatmap::ht_opt("HEATMAP_LEGEND_PADDING")
stopifnot(inherits(previous_gap, "unit"))
stopifnot(inherits(bundle, "rt_pam50_research_bundle"),
          identical(bundle$assessment, "POST_SELECTION_DESCRIPTIVE_ONLY"),
          inherits(bundle$paired_effects$heatmap, "HeatmapList"),
          identical(bundle$paired_effects$color_breaks,
                    bundle$six_contrasts$color_breaks),
          identical(bundle$paired_effects$legend_width_mm, 98),
          identical(bundle$six_contrasts$legend_width_mm, 98),
          identical(bundle$paired_effects$legend_title_font_pt, 8.5),
          identical(bundle$six_contrasts$legend_tick_font_pt, 8),
          identical(bundle$paired_effects$scale_policy,
                    "FULL_OBSERVED_RANGE_NO_CLIPPING"),
          identical(bundle$paired_effects$anchor_legend,
                    "GENE_ANCHOR_15_PER_GROUP_SHOWN_LEFT"),
          identical(bundle$six_contrasts$anchor_legend,
                    "GENE_ANCHOR_15_PER_GROUP_SHOWN_LEFT"))
scale_review <- rt_pam50_scale_diagnostic(bundle, neutral_fraction = 0.2)
stopifnot(inherits(scale_review$plot, "ggplot"),
          identical(scale_review$effect_cells, 600L),
          identical(scale_review$scientific_scope,
                    "POST_SELECTION_DESCRIPTIVE_ONLY"),
          identical(scale_review$full_scale_breaks,
                    bundle$paired_effects$color_breaks),
          identical(as.integer(scale_review$summary$effect_cells), c(240L, 360L)),
          all(scale_review$summary$within_neutral_count >= 0),
          all(scale_review$summary$within_neutral_fraction >= 0 &
              scale_review$summary$within_neutral_fraction <= 1))
all_values <- c(bundle$prepared$effects, bundle$prepared$contrasts)
stopifnot(abs(max(abs(all_values)) -
              scale_review$full_scale_breaks[3L]) < 1e-12)
bad_review <- try(rt_pam50_scale_diagnostic(
  bundle, neutral_fraction = 1), silent = TRUE)
stopifnot(inherits(bad_review, "try-error"))
bad_bundle <- bundle
bad_bundle$paired_effects$color_breaks <- c(-1, 0, 1)
stopifnot(inherits(try(rt_pam50_scale_diagnostic(bad_bundle),
                       silent = TRUE), "try-error"))

caption_a <- rt_pam50_manuscript_caption(bundle, "paired_effects")
caption_b <- rt_pam50_manuscript_caption(bundle, "six_contrasts")
stopifnot(grepl("106 matched", caption_a, fixed = TRUE),
          grepl("formal subtype analysis includes 106", caption_a, fixed = TRUE),
          !grepl("LumB .", caption_b, fixed = TRUE),
          grepl("LumB.", caption_b, fixed = TRUE),
          grepl("15-gene subtype-anchor", caption_b, fixed = TRUE),
          grepl("not an individual patient", caption_a, fixed = TRUE),
          grepl("first named subtype", caption_b, fixed = TRUE),
          grepl("Color does not encode significance or uncertainty", caption_a,
                fixed = TRUE))
stopifnot(inherits(try(rt_pam50_manuscript_caption(bundle, "unsupported"),
                       silent = TRUE), "try-error"))

folder <- "artifacts/ci_figure_review/pam50_research"
exports <- rt_export_pam50_research(
  bundle, output_dir = folder,
  source = "synthetic 60-gene aligned fixture, seed=711",
  data_status = "SYNTHETIC", width = 9, height = 13, dpi = 300L)
stopifnot(identical(ComplexHeatmap::ht_opt("HEATMAP_LEGEND_PADDING"), previous_gap))
stopifnot(length(exports) == 2L,
          exports$paired_effects$n_columns == 4L,
          exports$six_contrasts$n_columns == 6L,
          exports$paired_effects$n_features == 60L,
          exports$six_contrasts$n_features == 60L,
          exports$paired_effects$n_formal_subtype_pairs == 106L,
          identical(exports$paired_effects$sample_level_columns, FALSE),
          identical(exports$six_contrasts$inferential_status,
                    "POST_SELECTION_DESCRIPTIVE_ONLY"),
          identical(exports$paired_effects$legend_width_mm, 98),
          identical(exports$six_contrasts$legend_width_mm, 98),
          identical(exports$paired_effects$scale_policy,
                    "FULL_OBSERVED_RANGE_NO_CLIPPING"),
          identical(exports$paired_effects$color_breaks,
                    exports$six_contrasts$color_breaks),
          identical(exports$paired_effects$caption_review,
                    "PENDING_AUTHOR_AND_SCIENTIFIC_REVIEW"),
          identical(exports$paired_effects$internal_bottom_legend_gap_mm, 12),
          identical(exports$six_contrasts$internal_bottom_legend_gap_mm, 12),
          identical(exports$paired_effects$anchor_legend_alignment, "heatmap_top"),
          identical(exports$six_contrasts$anchor_legend,
                    "GENE_ANCHOR_15_PER_GROUP_SHOWN_LEFT"))
for (kind in c("paired_effects", "six_contrasts")) {
  stem <- file.path(folder, paste0("PAM50_", kind))
  stopifnot(all(file.exists(paste0(stem,
             c(".pdf", ".png", ".metadata.rds", ".metadata.json",
               ".caption.txt")))))
  caption_path <- paste0(stem, ".caption.txt")
  caption_text <- paste(readLines(caption_path, warn = FALSE), collapse = " ")
  stopifnot(grepl("106 matched", caption_text, fixed = TRUE),
            grepl("post-selection", tolower(caption_text), fixed = TRUE),
            identical(basename(exports[[kind]]$caption_file),
                      basename(caption_path)))
  audited <- rt_figure_audit(stem)
  stopifnot(identical(audited$automated_checks, "PASS"))
  if (!nzchar(Sys.which("pdftotext")))
    stop("Install Poppler pdftotext to confirm visible manuscript gene labels.")
  rendered_text <- suppressWarnings(system2(
    "pdftotext", args = c("-layout",
      shQuote(paste0(stem, ".pdf")), "-"), stdout = TRUE, stderr = TRUE))
  stopifnot(is.null(attr(rendered_text, "status")))
  expected_labels <- paste0("Synthetic_", seq_len(60L))
  stopifnot(all(vapply(expected_labels, function(gene)
    any(grepl(paste0("(^|[^[:alnum:]_])", gene,
                     "([^[:alnum:]_]|$)"), rendered_text,
              perl = TRUE)), logical(1))))
  stopifnot(any(grepl("Basal", rendered_text, fixed = TRUE)),
            any(grepl("LumB", rendered_text, fixed = TRUE)),
            any(grepl("Gene anchor", rendered_text, fixed = TRUE)))
}
diagnostic_stem <- file.path(folder, "PAM50_scale_diagnostic")
supplement <- rt_manuscript_export(
  scale_review$plot, diagnostic_stem,
  figure_id = "PAM50_Scale_Diagnostic",
  legend = paste("Descriptive distribution of 240 paired-effect",
                 "and 360 first-minus-second effect cells across frozen genes;",
                 "not patient observations or confidence intervals."),
  study = "Frozen PAM50 schematic synthetic validation",
  data_status = "SYNTHETIC",
  analysis_unit = "archived effect/contrast cell, not a patient",
  source = "Fully synthetic frozen-PAM50 fixture, seed 711",
  n_analyzed = 600L, n_missing = 0L,
  inference = "DESCRIPTIVE_ONLY", width = 8, height = 7, dpi = 300L
)
stopifnot(identical(supplement$n_analyzed, 600L),
          file.exists(paste0(diagnostic_stem, ".pdf")),
          file.exists(paste0(diagnostic_stem, ".png")),
          identical(rt_figure_audit(diagnostic_stem)$automated_checks, "PASS"))
cat("PAM50 research heatmaps and scale diagnostic PASS: 60x4, 60x6 and 600 effect cells\n")
