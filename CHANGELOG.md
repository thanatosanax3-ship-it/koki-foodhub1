# Changelog

## [Unreleased]
- Fix: adaptive outlier capping in `moving_average_forecast` so small historical series do not produce a fixed `100` forecast. (PR: fix/adaptive-forecasting)
- Add: per-product `trend`, `confidence` and `accuracy` in DB forecasts; add unit test to validate behavior.
- Docs: note forecasting behavior in `README.md`.
