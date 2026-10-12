# Explicit inferential plotting contracts for biomedical manuscripts.
# Author: Paul Skeffington. Prepared with OpenAI.
# No I/O or package installation on source.
rt_verified_forest <- function(data, term, estimate, lower, upper,
                               estimate_unit, interval_level = 0.95,
                               model_label, reference_label) {
  rt_require()
  required <- c(term, estimate, lower, upper)
  if (!is.data.frame(data) || !all(required %in% names(data)) ||
      anyDuplicated(as.character(data[[term]])) ||
      !is.character(data[[term]]) || anyNA(data[[term]]) ||
      !nrow(data)) stop("Supply unique, nonmissing term labels and aligned model columns.")
  if (!all(vapply(data[c(estimate, lower, upper)], is.numeric, logical(1))) ||
      any(!is.finite(as.matrix(data[c(estimate, lower, upper)]))) ||
      any(data[[lower]] > data[[estimate]] | data[[estimate]] > data[[upper]]))
    stop("Finite estimates and enclosing interval bounds required.")
  if (!is.numeric(interval_level) || length(interval_level) != 1L ||
      !is.finite(interval_level) || interval_level <= 0 || interval_level >= 1)
    stop("Declare valid interval coverage (0,1).")
  for (s in list(model_label, reference_label, estimate_unit))
    if (!is.character(s) || length(s) != 1L || is.na(s) || !nzchar(trimws(s)))
      stop("Complete model, reference and unit metadata required.")
  clean <- tibble::tibble(
    term = factor(data[[term]], levels = rev(data[[term]])),
    estimate = data[[estimate]], lower = data[[lower]], upper = data[[upper]]
  )
  ggplot2::ggplot(clean, ggplot2::aes(y = .data$term, x = .data$estimate)) +
    ggplot2::geom_vline(xintercept = 0, linetype = "dashed", colour = "#666666") +
    ggplot2::geom_errorbarh(ggplot2::aes(xmin = .data$lower, xmax = .data$upper),
                            height = 0.17, colour = "#0072B2") +
    ggplot2::geom_point(size = 2.4, colour = "#0072B2") +
    ggplot2::labs(
      title = model_label,
      subtitle = sprintf("%.1f%% intervals; reference: %s",
                         100 * interval_level, reference_label),
      x = rt_axis_label("Model estimate", estimate_unit), y = "Model term",
      caption = "Intervals supplied from independently verified model results; no intervals computed here."
    ) + rt_theme()
}

rt_verified_volcano <- function(data, feature, log2_effect, adjusted_p,
                                contrast, method, adjustment = "BH",
                                alpha = 0.05, threshold_log2 = 1) {
  rt_require()
  required <- c(feature, log2_effect, adjusted_p)
  if (!is.data.frame(data) || !nrow(data) || !all(required %in% names(data)) ||
      !is.character(data[[feature]]) || anyNA(data[[feature]]) ||
      anyDuplicated(data[[feature]]) ||
      !is.numeric(data[[log2_effect]]) || !is.numeric(data[[adjusted_p]]) ||
      any(!is.finite(data[[log2_effect]])) ||
      any(!is.finite(data[[adjusted_p]])) ||
      any(data[[adjusted_p]] < 0 | data[[adjusted_p]] > 1))
    stop("Require unique features and finite, verified log2 effect and adjusted p values.")
  if (!is.character(contrast) || length(contrast) != 1L || is.na(contrast) ||
      !nzchar(trimws(contrast)) || !is.character(method) ||
      length(method) != 1L || is.na(method) || !nzchar(trimws(method)) ||
      !is.character(adjustment) || length(adjustment) != 1L ||
      !adjustment %in% stats::p.adjust.methods)
    stop("Document contrast, tested model and valid multiplicity adjustment.")
  if (!is.numeric(alpha) || length(alpha) != 1L || !is.finite(alpha) ||
      alpha <= 0 || alpha >= 1 ||
      !is.numeric(threshold_log2) || length(threshold_log2) != 1L ||
      !is.finite(threshold_log2) || threshold_log2 < 0)
    stop("Declare valid FDR and magnitude thresholds.")
  # Zero adjusted p-values are numerical underflow, not infinite evidence.
  floor_p <- .Machine$double.xmin
  clean <- tibble::tibble(
    feature = data[[feature]], log2_effect = data[[log2_effect]],
    adjusted_p = data[[adjusted_p]],
    neg_log10 = -log10(pmax(data[[adjusted_p]], floor_p)),
    passes = data[[adjusted_p]] <= alpha &
             abs(data[[log2_effect]]) >= threshold_log2
  )
  ggplot2::ggplot(clean, ggplot2::aes(x = .data$log2_effect, y = .data$neg_log10)) +
    ggplot2::geom_point(ggplot2::aes(color = .data$passes), alpha = 0.7, size = 1.5) +
    ggplot2::geom_hline(yintercept = -log10(alpha), linetype = "dashed") +
    ggplot2::geom_vline(xintercept = c(-threshold_log2, threshold_log2),
                        linetype = "dotted") +
    ggplot2::scale_color_manual(values = c("FALSE" = "#777777",
                                             "TRUE" = "#0072B2"),
                                name = "Meets declared thresholds") +
    ggplot2::labs(
      title = paste("Volcano:", contrast),
      subtitle = sprintf("%s; %s adjustment; %d tested features; %d meet thresholds",
                         method, adjustment, nrow(clean), sum(clean$passes)),
      x = "Verified log2 effect (log2 units)",
      y = "−log10(adjusted p value)",
      caption = "Values supplied by validated inferential pipeline; zero p displayed at numerical floor."
    ) + rt_theme()
}
