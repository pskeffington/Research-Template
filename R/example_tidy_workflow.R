# Independently authored executable tidyverse pipeline. Synthetic data only.
# Author: Paul Skeffington. Prepared with OpenAI.
# Source R/research_tidy.R, R/research_plots.R, R/synthetic_demo.R first.
# Produces results in memory; does not save plots, install tools or send data.

run_tidy_example <- function(n = 90L, seed = 711L) {
  require_tidy_tools()
  rt_require()

  participants_source <- make_synthetic_cohort(n = n, seed = seed) |>
    dplyr::rename(
      Subject_ID = participant_id,
      Site = site,
      Age = age_years,
      Marker = measurement_mg_dl
    )

  # External source names are preserved in participants_source.
  participants_clean <- rename_source_columns(
    participants_source,
    c(participant_id = "Subject_ID", site = "Site",
      age_years = "Age", measurement_mg_dl = "Marker")
  )
  id_audit <- validate_join_keys(participants_clean, "participant_id")

  demographics_clean <- participants_clean |>
    dplyr::select(dplyr::all_of(c("participant_id", "site", "age_years")))
  measurements_clean <- participants_clean |>
    dplyr::select(dplyr::all_of(c("participant_id", "measurement_mg_dl")))

  analysis_ready <- join_research_tables(
    demographics_clean, measurements_clean,
    keys = "participant_id", relationship = "one-to-one", join = "left"
  )
  join_audit <- attr(analysis_ready, "join_audit")

  measurements_long <- pivot_measurements_longer(
    analysis_ready,
    id_columns = c("participant_id", "site"),
    measurement_columns = c("age_years", "measurement_mg_dl"),
    measurement_units = c(age_years = "years", measurement_mg_dl = "mg/dL")
  )
  measurements_wide <- pivot_measurements_wider(
    measurements_long, id_columns = c("participant_id", "site")
  )
  if (nrow(measurements_long) != 2L * nrow(analysis_ready) ||
      nrow(measurements_wide) != nrow(analysis_ready)) {
    stop("Reshaping changed the participant or measurement denominator.")
  }

  site_summary <- summarize_measurements(
    analysis_ready, measurement = "measurement_mg_dl",
    unit = "mg/dL", by = "site"
  )
  missingness_summary <- summarize_missingness(
    analysis_ready, c("age_years", "measurement_mg_dl")
  )

  # Explicit grammar of graphics: table -> aesthetics -> geometry -> labels/theme.
  observed_data <- analysis_ready |>
    dplyr::filter(
      !is.na(.data$age_years),
      !is.na(.data$measurement_mg_dl)
    ) |>
    dplyr::mutate(site = factor(
      .data$site, levels = c("North", "South", "West")
    ))

  p_relationship <- ggplot2::ggplot(
    observed_data,
    ggplot2::aes(
      x = .data$age_years,
      y = .data$measurement_mg_dl,
      color = .data$site,
      shape = .data$site
    )
  ) +
    ggplot2::geom_point(alpha = 0.75, size = 2) +
    ggplot2::scale_color_manual(
      values = stats::setNames(
        rt_palette()[1:3], c("North", "South", "West")
      ), drop = FALSE
    ) +
    ggplot2::labs(
      title = "Synthetic age and measurement",
      subtitle = sprintf("Complete pairs n=%d/%d",
                         nrow(observed_data), nrow(analysis_ready)),
      x = rt_axis_label("Age", "years"),
      y = rt_axis_label("Simulated measurement", "mg/dL"),
      color = "Enrollment site",
      shape = "Enrollment site",
      caption = "Synthetic descriptive data. No clinical, causal or inferential claim."
    ) +
    rt_theme()

  list(
    participants_source = participants_source,
    participants_clean = participants_clean,
    analysis_ready = analysis_ready,
    id_audit = id_audit,
    join_audit = join_audit,
    measurements_long = measurements_long,
    measurements_wide = measurements_wide,
    site_summary = site_summary,
    missingness_summary = missingness_summary,
    figure = p_relationship
  )
}
