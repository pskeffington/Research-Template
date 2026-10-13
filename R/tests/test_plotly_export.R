# Plotly's optional path is tested explicitly in CI, not silently skipped.
source("R/research_tidy.R")
source("R/research_plots.R")
source("R/research_interactive.R")
stopifnot(requireNamespace("plotly", quietly = TRUE),
          requireNamespace("htmlwidgets", quietly = TRUE))
x <- data.frame(category = c("Control", "Control", "Case", "Case"),
                measurement = c(1.2, 1.3, 2.1, 2.3))
p <- rt_box(x, "category", "measurement",
            y_name = "Synthetic measurement", y_unit = "unitless")
widget <- rt_interactive(p)
stopifnot(inherits(widget, "plotly"))
out <- "artifacts/ci_figure_review/plotly_synthetic.html"
rt_save_interactive(widget, out, data_status = "SYNTHETIC",
                    public_release_approved = FALSE)
stopifnot(file.exists(out), file.info(out)$size > 1000L,
          dir.exists(sub("\\.html$", "_files", out)),
          any(grepl("plotly", readLines(out, warn = FALSE), ignore.case = TRUE)))
denied <- try(rt_save_interactive(widget, tempfile(fileext = ".html"),
                                  data_status = "RESTRICTED",
                                  public_release_approved = TRUE),
              silent = TRUE)
stopifnot(inherits(denied, "try-error"))
double_write <- try(rt_save_interactive(widget, out,
                                        data_status = "SYNTHETIC"),
                    silent = TRUE)
stopifnot(inherits(double_write, "try-error"))
cat("Plotly conversion and local HTML export PASS; human disclosure review pending\n")
