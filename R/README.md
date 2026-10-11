# R companion — optional ggplot2 examples

R and ggplot2 are optional and not installed by the Python package. In an R session, install `ggplot2` separately according to your local dependency policy. Then:

```r
source("R/research_plots.R")
source("R/synthetic_demo.R")
demo <- rt_make_synthetic(n = 90L, seed = 711L)
p1 <- rt_scatter(demo, "age_years", "measurement_mg_dl",
                 x_name = "Age", x_unit = "years",
                 y_name = "Simulated measurement", y_unit = "mg/dL")
p2 <- rt_box(demo, "site", "measurement_mg_dl",
             y_name = "Simulated measurement", y_unit = "mg/dL")
print(p1); print(p2)
rt_save(p1, "artifacts/r/age_vs_measurement.pdf")
```

Function names and units are explicit. No source step downloads real data, installs packages, runs models or writes files. Only `rt_save` writes to a user-selected destination. These examples are descriptive, not validated inference or clinical claims. Follow [statistical workflow](../docs/STATISTICAL_WORKFLOW.md) before testing real observations.
