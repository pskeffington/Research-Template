# Frozen PAM50 schema alignment: entirely synthetic, without protected gene names.
source("R/research_tidy.R")
source("R/research_plots.R")
source("R/research_pam50_heatmaps.R")
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
    values[anchors == subtypes[s], s] + 3.0
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
stopifnot(inherits(bundle, "rt_pam50_research_bundle"),
          identical(bundle$assessment, "POST_SELECTION_DESCRIPTIVE_ONLY"),
          inherits(bundle$paired_effects$heatmap, "HeatmapList"),
          identical(bundle$paired_effects$color_breaks,
                    bundle$six_contrasts$color_breaks))
folder <- "artifacts/ci_figure_review/pam50_research"
exports <- rt_export_pam50_research(
  bundle, output_dir = folder,
  source = "synthetic 60-gene aligned fixture, seed=711",
  data_status = "SYNTHETIC", width = 9, height = 13, dpi = 300L)
stopifnot(length(exports) == 2L,
          exports$paired_effects$n_columns == 4L,
          exports$six_contrasts$n_columns == 6L,
          exports$paired_effects$n_features == 60L,
          exports$six_contrasts$n_features == 60L,
          exports$paired_effects$n_formal_subtype_pairs == 106L,
          identical(exports$paired_effects$sample_level_columns, FALSE),
          identical(exports$six_contrasts$inferential_status,
                    "POST_SELECTION_DESCRIPTIVE_ONLY"))
for (kind in c("paired_effects", "six_contrasts")) {
  stem <- file.path(folder, paste0("PAM50_", kind))
  stopifnot(all(file.exists(paste0(stem,
             c(".pdf", ".png", ".metadata.rds", ".metadata.json")))))
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
            any(grepl("LumB", rendered_text, fixed = TRUE)))
}
cat("PAM50 research heatmaps PASS: 60x4, 60x6, frozen rank, directional tests, 2 PDF/PNG artifacts\n")
