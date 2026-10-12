# Frozen discovery signature heatmaps: four paired subtype effects and six contrasts.
# Author: Paul Skeffington. Prepared with OpenAI.
# Research-specific schema only. Does not read private data or select genes.
# Source time is inert; all file I/O is explicitly invoked.

rt_pam50_profile <- function() {
  list(
    subtype_order = c("Basal", "Her2", "LumA", "LumB"),
    n_pairs = c(Basal = 16L, Her2 = 9L, LumA = 59L, LumB = 22L),
    contrasts = c("Basal_vs_LumA", "Her2_vs_LumA", "LumB_vs_LumA",
                  "Basal_vs_Her2", "Basal_vs_LumB", "Her2_vs_LumB"),
    expected_genes = 60L, genes_per_anchor = 15L,
    discovery_pairs = 109L, subtype_pairs = 106L,
    inference = "POST_SELECTION_DESCRIPTIVE_ONLY"
  )
}

rt_prepare_pam50_research <- function(signature, contrasts = NULL,
                                      tolerance = 1e-8) {
  profile <- rt_pam50_profile()
  subtypes <- profile$subtype_order
  columns <- paste0("logFC_", subtypes)
  fields <- c("gene_id", "SYMBOL", "anchor_subtype", "anchor_rank",
              "selected_signature", columns)
  if (!is.data.frame(signature) || nrow(signature) != 60L ||
      !all(fields %in% names(signature)))
    stop("Exactly 60 frozen ST09 rows and all identity/effect columns are required.")
  if (!is.numeric(tolerance) || length(tolerance) != 1L ||
      !is.finite(tolerance) || tolerance <= 0 || tolerance > 1e-6)
    stop("Supply a positive match tolerance no greater than 1e-6.")
  ids <- signature$gene_id
  anchors <- as.character(signature$anchor_subtype)
  ranks <- signature$anchor_rank
  chosen <- signature$selected_signature
  if (!is.character(ids) || anyNA(ids) || any(!nzchar(ids)) ||
      anyDuplicated(ids) || anyNA(anchors) ||
      !setequal(unique(anchors), subtypes) ||
      anyNA(ranks) || !is.numeric(ranks) ||
      any(!is.finite(ranks)) || any(ranks != as.integer(ranks)) ||
      !all(as.character(chosen) == "TRUE"))
    stop("ST09 gene identity, selected flag, anchor and ranks must be frozen.")
  if (!identical(unname(as.integer(table(factor(anchors, levels = subtypes)))),
                 rep(15L, 4L)))
    stop("Require exactly 15 frozen genes for each subtype anchor.")
  for (anchor in subtypes) {
    if (!identical(sort(as.integer(ranks[anchors == anchor])), seq_len(15L)))
      stop("Each anchor must retain frozen ranks 1 through 15.")
  }
  effect_values <- signature[columns]
  if (!all(vapply(effect_values, is.numeric, logical(1))) ||
      any(!is.finite(as.matrix(effect_values))))
    stop("All 240 ST09 paired effects must be finite numeric log2 values.")
  order_index <- order(match(anchors, subtypes), ranks, method = "radix")
  ordered <- signature[order_index, , drop = FALSE]
  effect_matrix <- as.matrix(ordered[columns])
  dimnames(effect_matrix) <- list(ordered$gene_id, subtypes)
  computed_anchor <- apply(effect_matrix, 1L, function(z) {
    subtypes[which.max(z)]
  })
  if (!identical(unname(computed_anchor),
                 as.character(ordered$anchor_subtype)))
    stop("Frozen gene anchor must equal its highest paired subtype effect.")
  gene_label <- as.character(ordered$SYMBOL)
  missing_symbol <- is.na(gene_label) | !nzchar(trimws(gene_label))
  gene_label[missing_symbol] <- ordered$gene_id[missing_symbol]
  duplicates <- duplicated(gene_label) | duplicated(gene_label, fromLast = TRUE)
  gene_label[duplicates] <- paste0(gene_label[duplicates], " [",
                                    ordered$gene_id[duplicates], "]")
  if (anyDuplicated(gene_label))
    stop("Gene labels must be unique after stable ID disambiguation.")
  row_anchor <- factor(as.character(ordered$anchor_subtype), levels = subtypes)
  pairwise_matrix <- NULL
  if (!is.null(contrasts)) {
    expected <- profile$contrasts
    necessary <- c("gene_id", "contrast", "logFC")
    if (!is.data.frame(contrasts) || nrow(contrasts) != 360L ||
        !all(necessary %in% names(contrasts)) ||
        !is.character(contrasts$gene_id) ||
        !is.character(contrasts$contrast) ||
        !is.numeric(contrasts$logFC) ||
        any(!is.finite(contrasts$logFC)) ||
        !setequal(unique(contrasts$gene_id), ids) ||
        !setequal(unique(contrasts$contrast), expected) ||
        anyDuplicated(paste(contrasts$gene_id, contrasts$contrast, sep = "\r")))
      stop("Exactly 360 unique frozen ST07 gene-by-contrast effects required.")
    expected_rows <- expand.grid(gene_id = ordered$gene_id,
                                 contrast = expected,
                                 stringsAsFactors = FALSE)
    keys <- paste(contrasts$gene_id, contrasts$contrast, sep = "\r")
    loc <- match(paste(expected_rows$gene_id, expected_rows$contrast,
                       sep = "\r"), keys)
    if (anyNA(loc)) stop("Every frozen gene must have all six contrasts.")
    if (all(c("first_subtype", "second_subtype") %in% names(contrasts))) {
      pairs <- strsplit(expected_rows$contrast, "_vs_", fixed = TRUE)
      first <- vapply(pairs, function(p) p[1L], character(1))
      second <- vapply(pairs, function(p) p[2L], character(1))
      if (!identical(as.character(contrasts$first_subtype[loc]), first) ||
          !identical(as.character(contrasts$second_subtype[loc]), second))
        stop("Source contrast direction must be first subtype minus second.")
    }
    contrast_value <- contrasts$logFC[loc]
    for (name in expected) {
      ab <- strsplit(name, "_vs_", fixed = TRUE)[[1L]]
      rows <- which(expected_rows$contrast == name)
      predicted <- effect_matrix[, ab[1L]] - effect_matrix[, ab[2L]]
      if (max(abs(contrast_value[rows] - predicted)) > tolerance)
        stop("ST07 contrast differs from first-minus-second ST09 effects.")
    }
    pairwise_matrix <- matrix(contrast_value,
                              nrow = length(ordered$gene_id),
                              ncol = length(expected),
                              dimnames = list(ordered$gene_id, expected))
  }
  list(
    effects = effect_matrix, contrasts = pairwise_matrix,
    gene_id = ordered$gene_id, gene_labels = gene_label,
    anchor = row_anchor, anchor_rank = ordered$anchor_rank,
    profile = profile, tolerance = tolerance,
    source_columns = columns, matrix_semantics = "gene_by_modeled_effect",
    sample_level_columns = FALSE
  )
}

rt_pam50_research_heatmaps <- function(signature, contrasts,
                                       tolerance = 1e-8,
                                       shared_scale = TRUE) {
  prepared <- rt_prepare_pam50_research(signature, contrasts, tolerance)
  if (!requireNamespace("ComplexHeatmap", quietly = TRUE) ||
      !requireNamespace("circlize", quietly = TRUE))
    stop("Install approved ComplexHeatmap and circlize to render PAM50 figures.")
  if (!exists("rt_palette", mode = "function"))
    stop("Source R/research_plots.R before this module.")
  if (!is.logical(shared_scale) || length(shared_scale) != 1L ||
      is.na(shared_scale))
    stop("shared_scale must be TRUE or FALSE.")
  profile <- prepared$profile
  vals <- c(prepared$effects, prepared$contrasts)
  lim <- max(abs(vals))
  if (lim <= 0) lim <- 1
  palette <- c("#2166AC", "#F7F7F7", "#B2182B")
  colors <- stats::setNames(rt_palette()[seq_along(profile$subtype_order)],
                            profile$subtype_order)
  anchor_color <- ComplexHeatmap::rowAnnotation(
    "Frozen anchor" = prepared$anchor,
    col = list("Frozen anchor" = colors),
    show_annotation_name = FALSE, show_legend = TRUE,
    annotation_legend_param = list(
      "Frozen anchor" = list(
        title = "Gene anchor (15 each)",
        title_gp = grid::gpar(fontsize = 8),
        labels_gp = grid::gpar(fontsize = 8),
        ncol = 1L)),
    simple_anno_size = grid::unit(3, "mm"))
  create <- function(matrix, kind) {
    bound <- if (shared_scale) lim else max(abs(matrix))
    if (bound <= 0) bound <- 1
    breaks <- c(-bound, 0, bound)
    gradient <- circlize::colorRamp2(breaks, palette)
    if (kind == "paired_effects") {
      label <- paste0(profile$subtype_order,
                      "\nn=", unname(profile$n_pairs), " pairs")
      heading <- "Frozen PAM50 paired effects"
      legend_title <- "Paired tumor - adjacent normal\nlog2 fold change"
      subtitle <- "Subtype effect (not individual samples)"
    } else {
      label <- gsub("_vs_", " - ", colnames(matrix), fixed = TRUE)
      heading <- "Six planned contrasts of paired effects"
      legend_title <- "Difference in paired subtype effects\nlog2 fold change"
      subtitle <- "Effect differences; descriptive view of frozen tests"
    }
    right <- ComplexHeatmap::Heatmap(
      matrix, name = kind, col = gradient,
      row_split = prepared$anchor,
      cluster_rows = FALSE, cluster_row_slices = FALSE,
      cluster_columns = FALSE, cluster_column_slices = FALSE,
      row_labels = prepared$gene_labels,
      row_names_side = "right",
      row_names_max_width = grid::unit(46, "mm"),
      show_row_names = TRUE,
      row_names_gp = grid::gpar(fontsize = 7.5),
      column_labels = label,
      column_names_gp = grid::gpar(fontsize = 8.5),
      column_names_rot = if (kind == "paired_effects") 0 else 35,
      column_title = heading,
      column_title_gp = grid::gpar(fontsize = 11, fontface = "bold"),
      row_title_gp = grid::gpar(fontsize = 9, fontface = "bold"),
      row_title_rot = 0,
      width = grid::unit(111, "mm"),
      rect_gp = grid::gpar(col = "#FFFFFF", lwd = 0.25),
      row_gap = grid::unit(2.5, "mm"),
      na_col = "#BFC6CD",
      show_heatmap_legend = TRUE,
      heatmap_legend_param = list(
        title = legend_title,
        at = breaks,
        labels = format(signif(breaks, 3L), trim = TRUE, scientific = FALSE),
        title_gp = grid::gpar(fontsize = 8.5, fontface = "plain"),
        labels_gp = grid::gpar(fontsize = 8),
        title_position = "topcenter",
        legend_width = grid::unit(98, "mm"),
        direction = "horizontal")
    )
    # Anchor track is genuinely gene-level; subtype columns are model summaries.
    list(
      heatmap = anchor_color + right,
      color_breaks = breaks,
      heading = heading, kind = kind, scale_caption = subtitle,
      gene_count = 60L, column_count = ncol(matrix),
      legend_title = legend_title,
      legend_width_mm = 98,
      legend_title_font_pt = 8.5,
      legend_tick_font_pt = 8,
      scale_policy = "FULL_OBSERVED_RANGE_NO_CLIPPING",
      anchor_legend = "GENE_ANCHOR_15_PER_GROUP_SHOWN_LEFT"
    )
  }
  structure(list(
    paired_effects = create(prepared$effects, "paired_effects"),
    six_contrasts = create(prepared$contrasts, "six_contrasts"),
    prepared = prepared, shared_scale = shared_scale,
    assessment = "POST_SELECTION_DESCRIPTIVE_ONLY"
  ), class = "rt_pam50_research_bundle")
}

# Captions are separate from the vector PDF: no overlays onto dense gene labels.
# They document the actual estimand, denominator and noninferential scope.
rt_pam50_manuscript_caption <- function(bundle, kind) {
  if (!inherits(bundle, "rt_pam50_research_bundle") ||
      !kind %in% c("paired_effects", "six_contrasts"))
    stop("A frozen PAM50 bundle and an approved figure kind are required.")
  profile <- bundle$prepared$profile
  if (!identical(sum(as.integer(profile$n_pairs)), 106L) ||
      !identical(profile$genes_per_anchor, 15L))
    stop("Figure caption denominators and anchor sizes do not match the frozen cohort.")
  cohort <- paste0(
    "The formal subtype analysis includes 106 matched ",
    "tumor/adjacent-normal patient pairs ",
    "(Basal n=16, Her2 n=9, LumA n=59, LumB n=22).")
  common <- paste(
    "Rows show 60 discovery-selected genes arranged in four immutable",
    "15-gene subtype-anchor blocks (Basal, Her2, LumA, LumB);",
    "genes follow frozen anchor rank, not expression clustering.",
    cohort,
    "Blue indicates a negative paired log2 effect or effect difference;",
    "red indicates a positive value; white is zero.",
    "Both panels use the same full-range symmetric zero-centered scale.",
    "Color does not encode significance or uncertainty.",
    "Post-selection descriptive visualization only;",
    "no confidence intervals, external replication, or clinical prediction."
  )
  if (kind == "paired_effects") {
    paste(
      "PAM50-stratified frozen 60-gene paired-effect heatmap.",
      "Each of the four columns is a modeled within-patient",
      "tumor-minus-adjacent-normal log2 fold-change estimate for one subtype,",
      "not an individual patient or unpaired tumor expression measurement.",
      common
    )
  } else {
    paste(
      "Six planned pairwise contrasts of the frozen PAM50-stratified",
      "60-gene paired-effect signature.",
      "Each column gives the first named subtype's paired log2 effect",
      "minus the second's, in this fixed order:",
      paste0(paste(profile$contrasts, collapse = ", "), "."),
      "These are differences between modeled paired effects,",
      "not independent patient measurements or standalone p-values.",
      common
    )
  }
}

# Reserve space specifically between bottom column labels and color legend.
# ComplexHeatmap's draw(padding=...) controls the OUTER canvas only; it does
# not add an internal gap between column labels and the bottom legend.
# This scoped option is restored on exit, including when rendering fails.
rt_draw_pam50_with_legend_gap <- function(heatmap,
                                           legend_gap_mm = 12) {
  if (!inherits(heatmap, "HeatmapList"))
    stop("Expected a frozen PAM50 HeatmapList.")
  if (!is.numeric(legend_gap_mm) || length(legend_gap_mm) != 1L ||
      is.na(legend_gap_mm) || !is.finite(legend_gap_mm) ||
      legend_gap_mm < 8 || legend_gap_mm > 25)
    stop("Bottom legend separation must be 8-25 mm.")
  previous <- ComplexHeatmap::ht_opt("HEATMAP_LEGEND_PADDING")
  on.exit(ComplexHeatmap::ht_opt(
    HEATMAP_LEGEND_PADDING = previous), add = TRUE)
  ComplexHeatmap::ht_opt(
    HEATMAP_LEGEND_PADDING = grid::unit(legend_gap_mm, "mm"))
  ComplexHeatmap::draw(
    heatmap, heatmap_legend_side = "bottom",
    annotation_legend_side = "left",
    align_annotation_legend = "heatmap_top",
    merge_legends = FALSE,
    padding = grid::unit(c(7, 6, 7, 6), "mm"))
}

rt_export_pam50_research <- function(bundle, output_dir,
                                     source, data_status = "PRIVATE",
                                     width = 9, height = 13,
                                     dpi = 300L) {
  if (!inherits(bundle, "rt_pam50_research_bundle"))
    stop("Expected a prepared frozen PAM50 research bundle.")
  if (!is.character(output_dir) || length(output_dir) != 1L ||
      is.na(output_dir) || !nzchar(trimws(output_dir)) ||
      !is.character(source) || length(source) != 1L ||
      is.na(source) || !nzchar(trimws(source)) ||
      !is.character(data_status) || length(data_status) != 1L ||
      is.na(data_status) || !nzchar(trimws(data_status)))
    stop("Output directory, source, and data status must be declared.")
  if (!is.numeric(width) || !is.numeric(height) || !is.numeric(dpi) ||
      any(lengths(list(width, height, dpi)) != 1L) ||
      any(!is.finite(c(width, height, dpi))) ||
      width < 7 || height < 10 || width > 30 || height > 30 || dpi < 300)
    stop("Large signature requires >=7 by 10 inches and >=300 dpi.")
  if (!requireNamespace("digest", quietly = TRUE))
    stop("Approved digest package required for release-auditable exports.")
  if (!requireNamespace("jsonlite", quietly = TRUE))
    stop("Approved jsonlite package required for release-auditable exports.")
  profile <- bundle$prepared$profile
  kinds <- c("paired_effects", "six_contrasts")
  all_files <- unlist(lapply(kinds, function(kind)
    file.path(output_dir,
              paste0("PAM50_", kind,
                     c(".pdf", ".png", ".metadata.rds", ".metadata.json", ".caption.txt")))),
    use.names = FALSE)
  if (any(file.exists(all_files)))
    stop("Refusing to overwrite existing manuscript figures.")
  dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)
  created <- character()
  completed <- FALSE
  on.exit(if (!completed && length(created)) unlink(created), add = TRUE)
  manifests <- list()
  for (kind in kinds) {
    element <- bundle[[kind]]
    stem <- file.path(output_dir, paste0("PAM50_", kind))
    paths <- paste0(stem, c(".pdf", ".png", ".metadata.rds", ".metadata.json", ".caption.txt"))
    if (capabilities("cairo")) {
      grDevices::cairo_pdf(paths[1], width = width, height = height)
    } else {
      grDevices::pdf(paths[1], width = width, height = height,
                     useDingbats = FALSE)
    }
    created <- c(created, paths[1])
    tryCatch(rt_draw_pam50_with_legend_gap(
      element$heatmap, legend_gap_mm = 12),
      finally = grDevices::dev.off())
    grDevices::png(paths[2], width = width, height = height,
                   units = "in", res = dpi,
                   type = if (capabilities("cairo")) "cairo" else "Xlib")
    created <- c(created, paths[2])
    tryCatch(rt_draw_pam50_with_legend_gap(
      element$heatmap, legend_gap_mm = 12),
      finally = grDevices::dev.off())
    note <- paste0("Frozen 60 genes (15 per anchor), ",
                   profile$subtype_pairs, " matched pairs. ",
                   "Subtype values represent tumor-minus-adjacent-normal effects. ",
                   "Post-selection descriptive only; no new intervals or tests.")
    if (kind == "six_contrasts")
      note <- paste0(note, " Contrast values are first-minus-second effects.")
    caption <- rt_pam50_manuscript_caption(bundle, kind)
    meta <- list(
      figure_id = paste0("PAM50_", kind),
      legend = note, source = source, data_status = data_status,
      manuscript_caption = caption,
      caption_review = "PENDING_AUTHOR_AND_SCIENTIFIC_REVIEW",
      caption_file = paths[5],
      figure_review = "PENDING_VISUAL_AND_SCIENTIFIC_REVIEW",
      public_release_requested = FALSE,
      inferential_status = "POST_SELECTION_DESCRIPTIVE_ONLY",
      statistical_unit = "model-based subtype effect",
      sample_level_columns = FALSE,
      n_features = 60L, n_columns = element$column_count,
      n_pairs_by_subtype = as.list(profile$n_pairs),
      n_primary_discovery_pairs = profile$discovery_pairs,
      n_formal_subtype_pairs = profile$subtype_pairs,
      selected_gene_count = 60L,
      gene_order = bundle$prepared$gene_id,
      gene_labels = bundle$prepared$gene_labels,
      anchor_order = profile$subtype_order,
      anchor_counts = as.list(stats::setNames(rep(15L, 4L),
                                             profile$subtype_order)),
      contrast_order = if (kind == "six_contrasts") profile$contrasts else NULL,
      subtype_order = profile$subtype_order,
      color_center = 0, color_breaks = element$color_breaks,
      legend_title = element$legend_title,
      legend_width_mm = element$legend_width_mm,
      legend_title_font_pt = element$legend_title_font_pt,
      legend_tick_font_pt = element$legend_tick_font_pt,
      scale_policy = element$scale_policy,
      anchor_legend = element$anchor_legend,
      shared_color_scale = bundle$shared_scale,
      transformation = "archived paired log2FC; no plotting transformation",
      n_missing_cells = 0L, width_in = width, height_in = height,
      outer_padding_mm = c(bottom = 7, left = 6, top = 7, right = 6),
      internal_bottom_legend_gap_mm = 12,
      anchor_legend_alignment = "heatmap_top",
      dpi = dpi, files = paths[1:2]
    )
    meta$sha256 <- vapply(paths[1:2], digest::digest,
                          character(1), file = TRUE, algo = "sha256")
    saveRDS(meta, paths[3])
    created <- c(created, paths[3])
    jsonlite::write_json(meta, paths[4], auto_unbox = TRUE, pretty = TRUE)
    created <- c(created, paths[4])
    writeLines(strwrap(caption, width = 105L),
               con = paths[5], useBytes = TRUE)
    created <- c(created, paths[5])
    manifests[[kind]] <- meta
  }
  completed <- TRUE
  invisible(manifests)
}
