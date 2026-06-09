# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog.

## [Unreleased]

### Added
- Created the detailed identified components list (`components`) to return individual macros, labels, and confidence metrics for each detected food item in the `/meals/analyze` endpoint.
- Served static files from `data/` directory at `/static` to make generated segmentation overlays and uploads accessible via URL.
- Added COCO dataset food classes (IDs 46-55: Banana, Apple, Sandwich, Orange, Broccoli, Carrot, Hot Dog, Pizza, Donut, Cake) to `FOOD_PROFILES` to support prediction from standard pre-trained YOLO11n weights.
- Added database performance indexes on `estimated_name` and `timestamp` columns in `meal_records`, and `meal_id` in `meal_components`.
- Added new integration test in `test_meals.py` verifying HTTP 400 response for invalid/corrupted upload images.

### Changed
- Shifted the custom food profiles database keys to be 0-indexed (`0` to `15` instead of `1` to `16`) to match YOLO's native 0-indexed class outputs.
- Enabled automatic reload and served standard host parameters on API startup.
- Configured database session connection to execute `PRAGMA foreign_keys = ON;` in SQLite to ensure referential integrity.
- Enabled database-level cascade deletes (`ondelete="CASCADE"`) on `MealComponent`'s foreign key `meal_id`.
- Refactored `/meals/analyze` to validate uploaded images, strip EXIF metadata for privacy, and raise HTTP 400 Bad Request on invalid/corrupted files.

