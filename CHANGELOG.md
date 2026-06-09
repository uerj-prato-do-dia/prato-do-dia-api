# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog.

## [Unreleased]

### Added
- Created the detailed identified components list (`components`) to return individual macros, labels, and confidence metrics for each detected food item in the `/meals/analyze` endpoint.
- Served static files from `data/` directory at `/static` to make generated segmentation overlays and uploads accessible via URL.
- Added COCO dataset food classes (IDs 46-55: Banana, Apple, Sandwich, Orange, Broccoli, Carrot, Hot Dog, Pizza, Donut, Cake) to `FOOD_PROFILES` to support prediction from standard pre-trained YOLO11n weights.

### Changed
- Shifted the custom food profiles database keys to be 0-indexed (`0` to `15` instead of `1` to `16`) to match YOLO's native 0-indexed class outputs.
- Enabled automatic reload and served standard host parameters on API startup.
