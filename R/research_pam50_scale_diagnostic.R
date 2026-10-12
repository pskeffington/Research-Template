# Auxiliary descriptive diagnostic for the frozen PAM50 manuscript heatmaps.
# Author: Paul Skeffington. Prepared with OpenAI.
# Source defines functions only. No protected data, file I/O or package setup.
#
# Neither heatmap column is a patient. Histogram counts represent modeled
# gene-by-subtype and gene-by-contrast effect cells (240 and 360), not
# independent samples, hypothesis tests or uncertainty intervals.

rt_pam50_scale_diagnostic <- function(bundle, neutral_fraction = 0.2,
                                      histogram_bins = 40L) {
  if (!inherits(bundle, "rt_pam50_research_bundle") ||
      !identical(bundle$assessment, "POST_SELECTION_DESCRIPTIVE_ONLY") ||
      !identical(bundle$shared_scale, TRUE))
    stop("Require a frozen descriptive PAM50 bundle with a shared scale.")
  if (!exists("rt_theme", mode = "function"))
    stop("Source R/research_plots.R before the PAM50 diagnostic.")
  rt_require()
  if (!is.numeric(neutral_fraction) || length(neutral_fraction) != 1L ||
      is.na(neutral_fraction) || !is.finite(neutral_fraction) ||
      neutral_fraction <= 0 || neutral_fraction >= 1)
    stop("Neutral range must be a declared fraction strictly between 0 and 1.")
  if (!is.numeric(histogram_bins) || length(histogram_bins) != 1L ||
      !is.finite(histogram_bins) || histogram_bins != as.integer(histogram_bins) ||
      histogram_bins < 10L || histogram_bins > 120L)
    stop("Histogram bins must be a whole number between 10 and 120.")
  effects <- bundle$prepared$effects
  contrasts <- bundle$prepared$contrasts
  if (!is.matrix(effects) || !identical(dim(effects), c(60L, 4L)) ||
      !is.matrix(contrasts) || !identical(dim(contrasts), c(60L, 6L)) ||
      any(!is.finite(effects)) || any(!is.finite(contrasts)))
    stop("Require complete 60x4 and 60x6 finite archived effects.")
  panels <- c("Subtype paired effects (240 cells)",
              "First-minus-second contrasts (360 cells)")
  breaks_paired <- bundle$paired_effects$color_breaks
  breaks_contrast <- bundle$six_contrasts$color_breaks
  if (!identical(breaks_paired, breaks_contrast) ||
      length(breaks_paired) != 3L ||
      !isTRUE(all.equal(breaks_paired[2L], 0)) ||
      !isTRUE(all.equal(breaks_paired[1L], -breaks_paired[3L])))
    stop("A comparable, exactly centered, shared full-range color scale is required.")
  limit <- breaks_paired[3L]
  if (!is.finite(limit) || limit <= 0) stop("The shared scale limit must be positive.")
  within <- neutral_fraction * limit
  values <- list(as.numeric(effects), as.numeric(contrasts))
  data <- data.frame(
    panel = factor(rep(panels, times = c(240L, 360L)), levels = panels),
    log2_effect = c(values[[1]], values[[2]])
  )
  summary <- do.call(rbind, lapply(seq_along(values), function(i) {
    v <- values[[i]]
    data.frame(
      panel = panels[i], effect_cells = as.integer(length(v)),
      minimum = min(v), maximum = max(v), median = stats::median(v),
      q05 = as.numeric(stats::quantile(v, 0.05, names = FALSE)),
      q95 = as.numeric(stats::quantile(v, 0.95, names = FALSE)),
      within_neutral_count = as.integer(sum(abs(v) <= within)),
      within_neutral_fraction = mean(abs(v) <= within),
      stringsAsFactors = FALSE
    )
  }))
  # Extend the bin boundary infinitesimally to include the observed extremes,
  # without clipping or re-scaling original data.
  bins <- seq(-limit * (1 + 1e-8), limit * (1 + 1e-8),
              length.out = histogram_bins + 1L)
  graph <- ggplot2::ggplot(data, ggplot2::aes(x = .data$log2_effect)) +
    ggplot2::geom_histogram(
      breaks = bins, color = "white", linewidth = 0.3,
      fill = "#2166AC", closed = "right") +
    ggplot2::geom_vline(xintercept = 0, color = "#212121", linewidth = 0.4) +
    ggplot2::geom_vline(
      xintercept = c(-within, within),
      color = "#B2182B", linetype = "dashed", linewidth = 0.4) +
    ggplot2::facet_wrap(~panel, ncol = 1L, scales = "fixed") +
    ggplot2::coord_cartesian(xlim = c(-limit, limit), expand = TRUE) +
    ggplot2::labs(
      title = "Frozen PAM50: full-range color scale review",
      subtitle = sprintf(
        "Same signed scale as primary heatmaps: %.2f to +%.2f; dashed lines mark +/- %.0f%% of the limit",
        -limit, limit, 100 * neutral_fraction),
      x = "Archived log2 effect or first-minus-second effect contrast",
      y = "Number of fitted effect cells",
      caption = paste(
        "Diagnostic only: bars count 240 subtype effects and 360 contrasts across 60 frozen genes.",
        "Values are correlated post-selection model outputs, NOT independent patients or uncertainty.",
        "No clipping, new normalization, model fitting or significance testing.",
        sep = "\n"
      )
    ) +
    rt_theme() +
    ggplot2::theme(
      strip.text = ggplot2::element_text(face = "bold", size = 9),
      plot.subtitle = ggplot2::element_text(size = 9),
      plot.caption = ggplot2::element_text(size = 8, lineheight = 1),
      panel.spacing = grid::unit(1, "lines")
    )
  list(
    plot = graph, summary = summary, effect_cells = 600L,
    full_scale_breaks = breaks_paired,
    neutral_fraction = neutral_fraction, neutral_limit = within,
    effect_vectors = "FROZEN_240_AND_360_NO_PATIENT_ROWS",
    scientific_scope = "POST_SELECTION_DESCRIPTIVE_ONLY",
    figure_status = "SUPPLEMENTARY_SCALE_DIAGNOSTIC_NOT_CLINICAL_INFERENCE"
  )
}
