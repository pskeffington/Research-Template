import pytest

from research_template.synthetic import make_cohort


def test_plots_smoke(tmp_path):
    pytest.importorskip("matplotlib")
    from research_template.plots import histogram, save_figure
    fig = histogram(make_cohort(), "age_years", name="Age", unit="years")
    out = save_figure(fig, tmp_path / "example.pdf")
    assert out.stat().st_size > 100


def test_ml_group_split_smoke():
    pytest.importorskip("sklearn")
    from research_template.ml import run_classification
    result = run_classification(make_cohort(n=240, seed=90), seed=90)
    assert result["train_unique_participants"] + result["test_unique_participants"] == 240
    assert "logistic" in result["metrics"] and "dummy_majority" in result["metrics"]
    assert 0 <= result["metrics"]["logistic"]["auroc"] <= 1
