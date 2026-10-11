import json

import pytest

from research_template.biomed import FigureKit, Study, Variable, synthetic_kit
from research_template.plots import heatmap as legacy_heatmap
from research_template.synthetic import make_cohort


def test_schema_has_complete_labels_and_types():
    rows = make_cohort()
    with pytest.raises(ValueError, match="unit"):
        Variable("Measurement", "")
    with pytest.raises(ValueError, match="Categorical"):
        Variable("Site", "mg/dL", kind="categorical")
    with pytest.raises(ValueError, match="Column"):
        FigureKit(rows, variables={"unknown": Variable("Unknown", "unitless")},
                  study=Study("Demo", "person", "synthetic"))
    with pytest.raises(ValueError, match="levels"):
        FigureKit(rows, variables={
            "site": Variable("Site", "category", "categorical", ("North",))
        }, study=Study("Demo", "person", "synthetic"))


def test_summary_from_schema():
    kit = synthetic_kit(make_cohort(n=120))
    overall = kit.summary("measurement_mg_dl")
    group = kit.summary("measurement_mg_dl", group="site")
    assert overall["n_total"] == 120
    assert overall["n_missing"] > 0
    assert [r["group"] for r in group["groups"]] == ["North", "South", "West"]
    with pytest.raises(ValueError, match="numeric"):
        kit.summary("site")


def test_every_one_call_figure_has_metadata_and_exports(tmp_path):
    pytest.importorskip("matplotlib")
    import matplotlib.pyplot as plt

    kit = synthetic_kit(make_cohort(n=120))
    figs = [
        kit.histogram("measurement_mg_dl"),
        kit.scatter("age_years", "measurement_mg_dl"),
        kit.scatter("age_years", "measurement_mg_dl", group="site"),
        kit.box("measurement_mg_dl", group="site"),
        kit.box("measurement_mg_dl", group="site", violin=True),
        kit.category_bar("site"),
        kit.missingness("age_years", "measurement_mg_dl"),
        kit.correlation_heatmap("age_years", "measurement_mg_dl"),
    ]
    for index, fig in enumerate(figs):
        meta = fig._research_meta
        assert meta["n_used"] + meta["n_excluded"] == meta["n_total"]
        assert meta["study"]["status"].startswith("SYNTHETIC")
        assert meta["variables"]
        files = kit.save(fig, tmp_path / f"f{index}", formats=("pdf", "svg"))
        assert len(files) == 3
        assert all(path.stat().st_size > 100 for path in files)
        recorded = json.loads(files[-1].read_text())
        assert all(item["sha256"] for item in recorded["files"])
        plt.close(fig)


def test_matrix_heatmap_center_missingness_and_legacy(tmp_path):
    pytest.importorskip("matplotlib")
    import matplotlib.pyplot as plt

    study = Study("Synthetic", "sample", "self generated")
    args = {"row_labels": ["a", "b"], "col_labels": ["s1", "s2"],
            "name": "Test", "unit": "unitless"}
    with pytest.raises(ValueError, match="explicit meaningful center"):
        FigureKit.matrix_heatmap([[1, 2], [0, -1]], study=study,
                                 mode="diverging", **args)
    with pytest.raises(ValueError, match="Infinity"):
        FigureKit.matrix_heatmap([[1, float("inf")], [0, -1]], study=study, **args)
    fig = FigureKit.matrix_heatmap(
        [[1, None], [-1, 0]], study=study, mode="diverging", center=0, **args
    )
    assert fig._research_meta["missing_cells"] == 1
    assert len(synthetic_kit(make_cohort()).save(fig, tmp_path / "heat")) == 3
    plt.close(fig)
    legacy = legacy_heatmap([[0, 1], [2, 3]], **args)
    assert legacy._research_meta["kind"] == "matrix_heatmap"
    plt.close(legacy)


def test_incomplete_call_fails_loudly():
    pytest.importorskip("matplotlib")
    kit = synthetic_kit(make_cohort())
    with pytest.raises(ValueError, match="numeric"):
        kit.histogram("site")
    with pytest.raises(ValueError, match="2–8"):
        kit.category_bar("participant_id")
    with pytest.raises(ValueError, match="stem"):
        kit.save(kit.histogram("age_years"), "figure.png")
