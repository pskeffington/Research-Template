# Deterministic synthetic paginated ComplexHeatmap proofs.
# Author: Paul Skeffington. Prepared with OpenAI.
source("R/research_tidy.R")
source("R/research_plots.R")
source("R/research_pam50_heatmaps.R")
source("R/research_pam50_journal_layouts.R")
source("R/research_pam50_journal_render.R")

profile <- rt_pam50_profile()
ids <- sprintf("SYN_G%03d", seq_len(60L))
subtypes <- profile$subtype_order
anchors <- rep(subtypes, each = 15L)
values <- matrix(0, nrow = 60L, ncol = 4L)
set.seed(711)
values[] <- stats::rnorm(240L, sd = 0.6)
for (i in seq_along(subtypes))
  values[anchors == subtypes[i], i] <- values[anchors == subtypes[i], i] + 7
signature <- data.frame(
  gene_id = ids, SYMBOL = paste0("Synthetic_", seq_len(60L)),
  anchor_subtype = anchors, anchor_rank = rep(seq_len(15L), 4L),
  selected_signature = TRUE, stringsAsFactors = FALSE)
for (i in seq_along(subtypes))
  signature[[paste0("logFC_", subtypes[i])]] <- values[, i]
pair_list <- strsplit(profile$contrasts, "_vs_", fixed = TRUE)
contrasts <- do.call(rbind, lapply(seq_along(pair_list), function(i) {
  a <- pair_list[[i]][1L]
  b <- pair_list[[i]][2L]
  data.frame(
    gene_id = ids, contrast = profile$contrasts[i],
    first_subtype = a, second_subtype = b,
    logFC = signature[[paste0("logFC_", a)]] -
            signature[[paste0("logFC_", b)]],
    stringsAsFactors = FALSE)
}))
bundle <- rt_pam50_research_heatmaps(signature, contrasts)
make_meta <- function(kind) {
  list(
    gene_order = bundle$prepared$gene_id,
    gene_labels = bundle$prepared$gene_labels,
    anchor_order = subtypes, subtype_order = subtypes,
    anchor_counts = as.list(stats::setNames(rep(15L, 4L), subtypes)),
    inferential_status = "POST_SELECTION_DESCRIPTIVE_ONLY",
    sample_level_columns = FALSE, n_formal_subtype_pairs = 106L,
    n_features = 60L, n_columns = if (kind == "paired") 4L else 6L,
    contrast_order = if (kind == "paired") NULL else profile$contrasts,
    scale_policy = "FULL_OBSERVED_RANGE_NO_CLIPPING",
    shared_color_scale = TRUE,
    figure_review = "PENDING_VISUAL_AND_SCIENTIFIC_REVIEW",
    caption_review = "PENDING_AUTHOR_AND_SCIENTIFIC_REVIEW",
    public_release_requested = FALSE, color_center = 0,
    color_breaks = bundle$paired_effects$color_breaks)
}
plan <- rt_pam50_journal_layout(
  make_meta("paired"), make_meta("contrasts"), "J03")
stopifnot(identical(plan$status, "R_LAYOUT_PLAN_ONLY_NOT_RENDERED"))
source_before <- serialize(bundle$prepared, NULL)
out <- "artifacts/ci_figure_review/pam50_journal/J03"
legend_before <- ComplexHeatmap::ht_opt("HEATMAP_LEGEND_PADDING")
names_before <- ComplexHeatmap::ht_opt("DIMNAME_PADDING")
proofs <- rt_pam50_journal_synthetic_proofs(bundle, plan, out)
stopifnot(length(proofs) == 4L,
          identical(source_before, serialize(bundle$prepared, NULL)),
          identical(ComplexHeatmap::ht_opt("HEATMAP_LEGEND_PADDING"),
                    legend_before),
          identical(ComplexHeatmap::ht_opt("DIMNAME_PADDING"), names_before))
for (record in proofs) {
  stopifnot(record$n_genes == 30L,
            record$n_columns %in% c(4L, 6L),
            length(record$gene_labels) == 30L,
            length(record$row_anchor_groups) == 2L,
            identical(record$color_breaks, plan$shared_color_breaks),
            identical(record$public_release, "BLOCKED"),
            identical(record$status,
                      "SYNTHETIC_REVIEW_PROOF_NOT_PRODUCTION_CERTIFIED"))
}
expect_failure <- function(expr) {
  if (!inherits(try(expr, silent = TRUE), "try-error"))
    stop("Journal synthetic guard admitted an unsafe proof.")
}
expect_failure(rt_pam50_journal_synthetic_proofs(bundle, plan, out))
bad_bundle <- bundle
bad_bundle$prepared$gene_id[1] <- "PRIVATE_GENE"
expect_failure(rt_pam50_journal_synthetic_proofs(
  bad_bundle, plan, tempfile("synthetic_guard")))
bad_bundle <- bundle
bad_bundle$six_contrasts$color_breaks <- c(-1, 0, 1)
expect_failure(rt_pam50_journal_page(
  bad_bundle, plan, "six_contrasts", 1L))
cat("SYNTHETIC 30-GENE COMPLEXHEATMAP PROOFS PASS: 4 vector PDF/PNG pairs, source and scale preserved\n")
