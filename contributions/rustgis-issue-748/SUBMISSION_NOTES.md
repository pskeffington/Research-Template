# Submission notes — RustGIS issue 748

This ZIP is synthetic only and includes an additive patch (delivered
separately) against the RustGIS working tree. To apply and test:

~~~sh
git apply --check --whitespace=error rustgis_issue_748_synthetic_field_validation.patch
git apply rustgis_issue_748_synthetic_field_validation.patch
python -m pip install -r tests/field_validation/requirements-reference.txt
python -m unittest discover -s tests/field_validation/tests -v
~~~

The current upstream-main patch target and previously executed engine
revisions are distinct. No latest-HEAD RustGIS CLI pass should be asserted
until it is built and executed at that exact commit.

The ZIP intentionally excludes the McDowell public GIS sources and all
McDowell-specific comparison/processing code. This is optional additional
coverage for issue #748, not a feature change or source repair.
