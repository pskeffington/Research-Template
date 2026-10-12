# Condition-first complex heatmaps for annotated biomedical matrices.
# Author: Paul Skeffington. Prepared with OpenAI.
# Source only defines functions. No downloads, package installation, or I/O.
rt_prepare_complex_heatmap <- function(values, sample_metadata,
                                       sample_id = "sample_id",
                                       condition = "condition",
                                       condition_levels,
                                       annotations = character(),
                                       within_condition = NULL) {
  if (!is.matrix(values) || !is.numeric(values) || !length(values) ||
      any(is.infinite(values)) || all(is.na(values)) ||
      is.null(rownames(values)) || is.null(colnames(values)) ||
      anyNA(rownames(values)) || anyNA(colnames(values)) ||
      any(!nzchar(rownames(values))) || any(!nzchar(colnames(values))) ||
      anyDuplicated(rownames(values)) || anyDuplicated(colnames(values)))
    stop("Provide a numeric feature x sample matrix with unique nonempty identifiers and finite/NA cells.")
  if (!is.data.frame(sample_metadata) ||
      !is.character(sample_id) || length(sample_id) != 1L ||
      !is.character(condition) || length(condition) != 1L ||
      identical(sample_id, condition) ||
      !all(c(sample_id, condition) %in% names(sample_metadata)))
    stop("Sample metadata must supply distinct ID and condition columns.")
  ids <- sample_metadata[[sample_id]]
  groups <- sample_metadata[[condition]]
  if (!is.character(ids) || anyNA(ids) || any(!nzchar(ids)) ||
      anyDuplicated(ids) || !setequal(ids, colnames(values)) ||
      length(ids) != ncol(values) ||
      anyNA(groups) || any(!nzchar(as.character(groups))))
    stop("Exactly one metadata row is required per sample and every condition must be known.")
  if (!is.character(condition_levels) || !length(condition_levels) ||
      anyNA(condition_levels) || any(!nzchar(condition_levels)) ||
      anyDuplicated(condition_levels) ||
      !setequal(condition_levels, unique(as.character(groups))))
    stop("Declare all observed condition levels, exactly once, in publication order.")
  if (!is.character(annotations) || anyNA(annotations) ||
      anyDuplicated(annotations) ||
      any(annotations %in% c(sample_id, condition)) ||
      !all(annotations %in% names(sample_metadata)) ||
      length(annotations) > 6L)
    stop("Declare up to six distinct additional annotation columns.")
  if (!is.null(within_condition) &&
      (!is.character(within_condition) || length(within_condition) != 1L ||
       is.na(within_condition) ||
       !within_condition %in% names(sample_metadata)))
    stop("Within-condition ordering must name a metadata column.")
  aligned <- sample_metadata[match(colnames(values), ids), , drop = FALSE]
  if (!is.null(within_condition)) {
    sort_by <- aligned[[within_condition]]
    if (anyNA(sort_by) || !(is.numeric(sort_by) || is.character(sort_by) ||
                             is.factor(sort_by) || inherits(sort_by, "Date")))
      stop("Within-condition ordering must be complete numeric, date or categorical data.")
  } else {
    sort_by <- seq_len(ncol(values))
  }
  ordered <- order(match(as.character(aligned[[condition]]), condition_levels),
                   sort_by, seq_len(ncol(values)), method = "radix")
  aligned <- aligned[ordered, , drop = FALSE]
  aligned[[condition]] <- factor(as.character(aligned[[condition]]),
                                  levels = condition_levels)
  for (field in annotations) {
    x <- aligned[[field]]
    if (!(is.character(x) || is.factor(x)) ||
        any(!nzchar(as.character(x[!is.na(x)]))))
      stop("Supplementary annotations must be nonempty categorical values or NA.")
    levels_observed <- if (is.factor(x)) levels(x) else sort(unique(x[!is.na(x)]))
    if (length(levels_observed) > 8L)
      stop("Each categorical annotation is limited to eight explicitly color-coded levels.")
    aligned[[field]] <- factor(as.character(x), levels = levels_observed)
  }
  list(
    values = values[, ordered, drop = FALSE],
    sample_metadata = aligned,
    sample_id = sample_id, condition = condition,
    condition_levels = condition_levels, annotations = annotations,
    sample_order = colnames(values)[ordered],
    n_missing = sum(is.na(values)),
    condition_counts = stats::setNames(
      as.integer(table(aligned[[condition]])), condition_levels)
  )
}

rt_complex_heatmap <- function(values, sample_metadata, condition_levels,
                               measurement, unit, value_transform,
                               sample_id = "sample_id", condition = "condition",
                               annotations = character(), within_condition = NULL,
                               mode = c("sequential", "diverging"), center = NULL,
                               show_row_names = nrow(values) <= 65L,
                               show_column_names = ncol(values) <= 45L,
                               rasterize = FALSE) {
  prep <- rt_prepare_complex_heatmap(
    values, sample_metadata, sample_id, condition, condition_levels,
    annotations, within_condition)
  if (!requireNamespace("ComplexHeatmap", quietly = TRUE) ||
      !requireNamespace("circlize", quietly = TRUE))
    stop("ComplexHeatmap and circlize are optional required packages for this plot.")
  if (!exists("rt_axis_label", mode = "function"))
    stop("Source R/research_plots.R before this module.")
  legend_title <- rt_axis_label(measurement, unit)
  if (!is.character(value_transform) || length(value_transform) != 1L ||
      is.na(value_transform) || !nzchar(trimws(value_transform)))
    stop("Describe normalization or transformation explicitly; use 'none' if raw.")
  for (flag in list(show_row_names, show_column_names, rasterize))
    if (!is.logical(flag) || length(flag) != 1L || is.na(flag))
      stop("Row/column label and rasterization flags must be scalar logicals.")
  mode <- match.arg(mode)
  if (mode == "diverging") {
    if (!is.numeric(center) || length(center) != 1L ||
        !is.finite(center)) stop("Signed scale requires an explicit finite center.")
  } else if (!is.null(center)) {
    stop("Sequential scale does not accept a center.")
  }
  observed <- prep$values[!is.na(prep$values)]
  if (mode == "diverging") {
    bound <- max(abs(observed - center))
    if (bound == 0) bound <- 1
    breaks <- c(center - bound, center, center + bound)
    colors <- c("#2166AC", "#F7F7F7", "#B2182B")
  } else {
    limits <- range(observed)
    if (limits[1] == limits[2]) {
      eps <- max(abs(limits[1]) * 1e-6, 1e-6)
      limits <- limits + c(-eps, eps)
    }
    breaks <- limits
    colors <- c("#F7FBFF", "#08519C")
  }
  colormap <- circlize::colorRamp2(breaks, colors)
  annotation_fields <- c(condition, annotations)
  annotation_data <- prep$sample_metadata[annotation_fields]
  annotation_colors <- lapply(annotation_data, function(field) {
    levels <- levels(field)
    if (length(levels) > 8L) stop("No more than eight category colors per annotation.")
    stats::setNames(rt_palette()[seq_along(levels)], levels)
  })
  names(annotation_colors) <- annotation_fields
  ha <- ComplexHeatmap::HeatmapAnnotation(
    df = annotation_data, col = annotation_colors,
    na_col = "#BFC6CD", show_annotation_name = TRUE)
  ht <- ComplexHeatmap::Heatmap(
    prep$values, name = legend_title, col = colormap,
    top_annotation = ha, na_col = "#BFC6CD",
    column_split = prep$sample_metadata[[condition]],
    cluster_columns = FALSE, cluster_column_slices = FALSE,
    cluster_rows = FALSE, cluster_row_slices = FALSE,
    show_row_names = show_row_names,
    show_column_names = show_column_names,
    column_names_rot = 90,
    row_names_gp = grid::gpar(fontsize = 7),
    column_names_gp = grid::gpar(fontsize = 7),
    column_title = measurement,
    heatmap_legend_param = list(
      title = paste(strwrap(legend_title, width = 21L), collapse = "\n")),
    use_raster = rasterize
  )
  structure(list(heatmap = ht, prepared = prep,
    measurement = measurement, unit = unit, transform = value_transform,
    mode = mode, center = center, breaks = breaks,
    show_row_names = show_row_names, show_column_names = show_column_names,
    rasterize = rasterize), class = "rt_complex_heatmap")
}

rt_export_complex_heatmap <- function(bundle, output_stem, figure_id, legend,
                                      source, data_status, width = 9,
                                      height = 7, dpi = 600L,
                                      public_release_approved = FALSE) {
  if (!inherits(bundle, "rt_complex_heatmap"))
    stop("Expected rt_complex_heatmap bundle.")
  fields <- list(output_stem, figure_id, legend, source, data_status)
  if (any(vapply(fields, function(x) !is.character(x) || length(x) != 1L ||
                 is.na(x) || !nzchar(trimws(x)), logical(1))) ||
      !grepl("^[A-Za-z0-9_.-]+$", figure_id))
    stop("Complete safe figure ID and provenance metadata required.")
  if (!is.logical(public_release_approved) ||
      length(public_release_approved) != 1L || is.na(public_release_approved))
    stop("Public release flag must be TRUE or FALSE.")
  if (public_release_approved &&
      grepl("PRIVATE|RESTRICTED|PHI", data_status, ignore.case = TRUE))
    stop("Private or restricted data cannot be marked approved for public release.")
  if (any(!is.finite(c(width, height, dpi))) ||
      width <= 0 || height <= 0 || dpi < 300 || width > 30 || height > 30)
    stop("Use positive printable dimensions <= 30 inches and >= 300 dpi.")
  if (grepl("[\\\\/]$", output_stem) || !nzchar(basename(output_stem)))
    stop("Output stem must include a basename.")
  files <- paste0(output_stem, c(".pdf", ".png", ".metadata.rds",
                                  ".metadata.json"))
  if (any(file.exists(files))) stop("Refusing to overwrite figure artifacts.")
  dir.create(dirname(output_stem), recursive = TRUE, showWarnings = FALSE)
  complete <- FALSE
  on.exit(if (!complete) unlink(files), add = TRUE)
  if (capabilities("cairo")) {
    grDevices::cairo_pdf(files[1], width = width, height = height)
  } else {
    grDevices::pdf(files[1], width = width, height = height,
                   useDingbats = FALSE)
  }
  tryCatch(ComplexHeatmap::draw(bundle$heatmap, heatmap_legend_side = "bottom",
                                annotation_legend_side = "right"),
           finally = grDevices::dev.off())
  grDevices::png(files[2], width = width, height = height, units = "in",
                 res = dpi, type = if (capabilities("cairo")) "cairo" else "Xlib")
  tryCatch(ComplexHeatmap::draw(bundle$heatmap, heatmap_legend_side = "bottom",
                                annotation_legend_side = "right"),
           finally = grDevices::dev.off())
  p <- bundle$prepared
  meta <- list(figure_id = figure_id, legend = legend, source = source,
    data_status = data_status, figure_review = "PENDING_VISUAL_AND_SCIENTIFIC_REVIEW",
    public_release_requested = public_release_approved,
    measurement = bundle$measurement, unit = bundle$unit,
    transform = bundle$transform, mode = bundle$mode, center = bundle$center,
    color_breaks = bundle$breaks,
    n_features = nrow(p$values), n_samples = ncol(p$values),
    n_missing_cells = p$n_missing,
    sample_order = p$sample_order, condition_levels = p$condition_levels,
    condition_counts = p$condition_counts, annotations = p$annotations,
    row_names_shown = bundle$show_row_names,
    column_names_shown = bundle$show_column_names,
    pdf_body_rasterized = bundle$rasterize,
    width_in = width, height_in = height, dpi = dpi,
    files = files[1:2], package_version = as.character(
      utils::packageVersion("ComplexHeatmap")))
  if (requireNamespace("digest", quietly = TRUE))
    meta$sha256 <- vapply(files[1:2], digest::digest,
                          character(1), file = TRUE, algo = "sha256")
  saveRDS(meta, files[3])
  if (requireNamespace("jsonlite", quietly = TRUE))
    jsonlite::write_json(meta, files[4], auto_unbox = TRUE, pretty = TRUE)
  complete <- TRUE
  invisible(meta)
}
