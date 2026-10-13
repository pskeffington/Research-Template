# Synthetic-only journal ComplexHeatmap render proofs, not submission artwork.
# Author: Paul Skeffington. Prepared with OpenAI.
# No source-time execution or protected research data.
rt_pam50_journal_page <- function(bundle, plan, kind, page_number) {
  if (!inherits(bundle, "rt_pam50_research_bundle") ||
      !identical(bundle$assessment, "POST_SELECTION_DESCRIPTIVE_ONLY") ||
      !isTRUE(bundle$shared_scale))
    stop("Require descriptive frozen-effect bundle and common color scale.")
  if (!is.list(plan) ||
      !identical(plan$status, "R_LAYOUT_PLAN_ONLY_NOT_RENDERED") ||
      !identical(plan$public_release, "BLOCKED") ||
      !kind %in% c("paired_effects", "six_contrasts") ||
      !page_number %in% c(1L, 2L))
    stop("Require a pending, two-page journal scenario.")
  if (!requireNamespace("ComplexHeatmap", quietly = TRUE) ||
      !requireNamespace("circlize", quietly = TRUE) ||
      !requireNamespace("digest", quietly = TRUE))
    stop("ComplexHeatmap, circlize and digest are required for page proofs.")
  ids <- bundle$prepared$gene_id
  labels <- bundle$prepared$gene_labels
  if (!is.character(ids) || length(ids) != 60L || anyDuplicated(ids) ||
      !is.character(labels) || length(labels) != 60L || anyDuplicated(labels))
    stop("Frozen 60-gene identity invalid.")
  if (!identical(
    digest::digest(paste(ids, collapse = "\n"), algo = "sha256",
                   serialize = FALSE),
    plan$complete_gene_order_sha256))
    stop("Planning gene hash differs from frozen effect bundle.")
  if (!identical(as.numeric(bundle$paired_effects$color_breaks),
                 as.numeric(plan$shared_color_breaks)) ||
      !identical(bundle$paired_effects$color_breaks,
                 bundle$six_contrasts$color_breaks) ||
      !identical(as.character(plan$shared_color_palette),
                 c("#2166AC", "#F7F7F7", "#B2182B")))
    stop("Color-scale lock or signed palette changed.")
  profile <- c("Basal", "Her2", "LumA", "LumB")
  contrasts <- c("Basal_vs_LumA", "Her2_vs_LumA", "LumB_vs_LumA",
                 "Basal_vs_Her2", "Basal_vs_LumB", "Her2_vs_LumB")
  if (!identical(colnames(bundle$prepared$effects), profile) ||
      !identical(colnames(bundle$prepared$contrasts), contrasts) ||
      !identical(dim(bundle$prepared$effects), c(60L, 4L)) ||
      !identical(dim(bundle$prepared$contrasts), c(60L, 6L)))
    stop("Cannot re-label or remove modeled effect columns.")
  rows <- if (page_number == 1L) seq_len(30L) else 31:60
  section <- plan$pages[[page_number]]
  if (!identical(as.integer(c(section$row_start, section$row_end)),
                 as.integer(range(rows))) ||
      !identical(as.integer(section$rows), 30L) ||
      !identical(digest::digest(paste(ids[rows], collapse = "\n"),
                                algo = "sha256", serialize = FALSE),
                 section$gene_order_sha256))
    stop("Page boundaries or gene order were modified.")
  group <- factor(as.character(bundle$prepared$anchor[rows]), levels = profile)
  if (!identical(as.character(group), rep(section$anchors, each = 15L)))
    stop("Page must retain two contiguous 15-gene anchor blocks.")
  matrix <- if (kind == "paired_effects") bundle$prepared$effects
            else bundle$prepared$contrasts
  panel <- matrix[rows, , drop = FALSE]
  if (any(!is.finite(panel)) || !identical(rownames(panel), ids[rows]))
    stop("Page contains missing or misordered frozen effect estimates.")
  column_text <- if (kind == "paired_effects")
    paste0(profile, "\nn=", unname(bundle$prepared$profile$n_pairs), " pairs")
  else gsub("_vs_", "\nvs\n", contrasts, fixed = TRUE)
  gradient <- circlize::colorRamp2(
    as.numeric(plan$shared_color_breaks), plan$shared_color_palette)
  anchor_colors <- stats::setNames(
    c("#0072B2", "#D55E00", "#009E73", "#CC79A7"), profile)
  anchor <- ComplexHeatmap::rowAnnotation(
    "Anchor" = group,
    col = list("Anchor" = anchor_colors),
    show_annotation_name = FALSE, show_legend = FALSE,
    simple_anno_size = grid::unit(3, "mm"))
  breaks <- as.numeric(plan$shared_color_breaks)
  right <- ComplexHeatmap::Heatmap(
    panel, name = kind, col = gradient,
    row_split = group, cluster_rows = FALSE, cluster_row_slices = FALSE,
    cluster_columns = FALSE, cluster_column_slices = FALSE,
    row_labels = labels[rows], row_names_side = "right",
    row_names_max_width = grid::unit(43, "mm"),
    row_names_gp = grid::gpar(fontsize = section$label_font_pt),
    show_row_names = TRUE,
    row_title_gp = grid::gpar(fontsize = 9.5, fontface = "bold"),
    row_title_rot = 0,
    column_labels = column_text, column_names_side = "bottom",
    column_names_rot = 0,
    column_names_gp = grid::gpar(fontsize = section$column_font_pt),
    column_title = paste0("PAM50 modeled ", gsub("_", " ", kind, fixed = TRUE),
                          " | synthetic page ", page_number, " of 2"),
    column_title_gp = grid::gpar(fontsize = 10, fontface = "bold"),
    width = grid::unit(86, "mm"),
    rect_gp = grid::gpar(col = "#FFFFFF", lwd = 0.3),
    row_gap = grid::unit(3, "mm"),
    show_heatmap_legend = TRUE,
    heatmap_legend_param = list(
      title = "Signed log2 effect\nnegative / zero / positive",
      at = breaks,
      labels = sprintf("%+.2f", breaks),
      labels_gp = grid::gpar(fontsize = section$legend_tick_font_pt),
      title_gp = grid::gpar(fontsize = 8.5),
      title_position = "topcenter",
      legend_width = grid::unit(75, "mm"),
      direction = "horizontal"))
  list(
    heatmap = anchor + right, page = as.integer(page_number),
    kind = kind, ids = ids[rows], labels = labels[rows],
    anchor_groups = section$anchors,
    column_count = ncol(panel),
    scale_breaks = breaks,
    source_gene_sha256 = section$gene_order_sha256)
}

rt_pam50_journal_synthetic_proofs <- function(bundle, plan, output_dir) {
  if (!is.character(output_dir) || length(output_dir) != 1L ||
      is.na(output_dir) || !nzchar(trimws(output_dir)) ||
      !grepl("^J0[1345]$", plan$journal_scenario))
    stop("Require an explicit four-scenario review-only output.")
  if (!is.character(bundle$prepared$gene_id) ||
      !identical(bundle$prepared$gene_id,
                 sprintf("SYN_G%03d", seq_len(60L))))
    stop("Only fully synthetic IDs can be rendered by this CI proof function.")
  if (!requireNamespace("jsonlite", quietly = TRUE) ||
      !requireNamespace("digest", quietly = TRUE))
    stop("JSON and SHA-256 are required for audited synthetic proofs.")
  items <- c("paired_effects", "six_contrasts")
  paths <- unlist(lapply(items, function(k)
    vapply(1:2, function(i) file.path(
      output_dir, sprintf("SYN_%s_%s_p%d", plan$journal_scenario, k, i)),
      character(1))), use.names = FALSE)
  files <- as.vector(outer(paths, c(".pdf", ".png", ".metadata.json"),
                           paste0))
  if (any(file.exists(files))) stop("Refusing to overwrite a proof or its metadata.")
  dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)
  made <- character()
  done <- FALSE
  on.exit(if (!done) unlink(made), add = TRUE)
  result <- list()
  for (kind in items) for (i in 1:2) {
    element <- rt_pam50_journal_page(bundle, plan, kind, i)
    stem <- file.path(output_dir,
                      sprintf("SYN_%s_%s_p%d", plan$journal_scenario, kind, i))
    pdf <- paste0(stem, ".pdf")
    png <- paste0(stem, ".png")
    metadata_path <- paste0(stem, ".metadata.json")
    previous_legend <- ComplexHeatmap::ht_opt("HEATMAP_LEGEND_PADDING")
    previous_names <- ComplexHeatmap::ht_opt("DIMNAME_PADDING")
    draw_page <- function() {
      on.exit(ComplexHeatmap::ht_opt(
        HEATMAP_LEGEND_PADDING = previous_legend,
        DIMNAME_PADDING = previous_names), add = TRUE)
      ComplexHeatmap::ht_opt(
        HEATMAP_LEGEND_PADDING = grid::unit(12, "mm"),
        DIMNAME_PADDING = grid::unit(6, "mm"))
      ComplexHeatmap::draw(
        element$heatmap, heatmap_legend_side = "bottom",
        merge_legends = FALSE,
        padding = grid::unit(c(7, 7, 8, 7), "mm"))
    }
    if (capabilities("cairo"))
      grDevices::cairo_pdf(pdf, width = plan$page_width_in,
                           height = plan$page_height_in)
    else
      grDevices::pdf(pdf, width = plan$page_width_in,
                     height = plan$page_height_in, useDingbats = FALSE)
    made <- c(made, pdf)
    tryCatch(draw_page(), finally = grDevices::dev.off())
    grDevices::png(png, width = plan$page_width_in,
                   height = plan$page_height_in, units = "in", res = 300L,
                   type = if (capabilities("cairo")) "cairo" else "Xlib")
    made <- c(made, png)
    tryCatch(draw_page(), finally = grDevices::dev.off())
    meta <- list(
      status = "SYNTHETIC_REVIEW_PROOF_NOT_PRODUCTION_CERTIFIED",
      figure_review = "PENDING_VISUAL_AND_SCIENTIFIC_REVIEW",
      journal_scenario = plan$journal_scenario,
      kind = kind, page = as.integer(i),
      gene_order = element$ids,
      gene_labels = element$labels,
      row_anchor_groups = element$anchor_groups,
      n_genes = 30L, n_columns = element$column_count,
      planned_genes_sha256 = element$source_gene_sha256,
      color_breaks = element$scale_breaks,
      color_palette = plan$shared_color_palette,
      signed_scale = "negative / zero / positive",
      width_in = plan$page_width_in,
      height_in = plan$page_height_in,
      expected_label_font_pt = 9,
      png_dpi = 300L,
      pdf_sha256 = digest::digest(pdf, file = TRUE, algo = "sha256"),
      png_sha256 = digest::digest(png, file = TRUE, algo = "sha256"),
      public_release = "BLOCKED")
    jsonlite::write_json(meta, metadata_path,
                         pretty = TRUE, auto_unbox = TRUE)
    made <- c(made, metadata_path)
    result[[basename(stem)]] <- meta
  }
  done <- TRUE
  invisible(result)
}
