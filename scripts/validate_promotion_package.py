#!/usr/bin/env python3
"""Validate a content-only promotion package with platform recommendations and adaptations."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


MODES = {
    "COMPLETE_PROMOTION_PACKAGE",
    "IMAGE_TEXT_PACKAGE",
    "SHORT_VIDEO_PACKAGE",
    "PRODUCT_STORY_PACKAGE",
    "PLATFORM_ADAPTATION_PACKAGE",
    "SINGLE_ASSET",
}
REGIONS = {"DOMESTIC", "OVERSEAS", "DUAL"}
MODELS = {"TOC", "TOB", "HYBRID"}

FORBIDDEN_KEYS = {
    "calendar",
    "publishing_calendar",
    "publishing_schedule",
    "posting_schedule",
    "schedule",
    "conversion",
    "conversion_paths",
    "conversion_funnel",
    "funnel",
    "cta",
    "destination",
    "metrics",
    "kpis",
    "experiments",
    "review",
    "retrospective",
    "stop_conditions",
    "external_actions",
}


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, path: str, message: str) -> None:
        self.errors.append(f"{path}: {message}")

    def warn(self, path: str, message: str) -> None:
        self.warnings.append(f"{path}: {message}")


def text_value(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def require_object(parent: dict[str, Any], key: str, report: Report) -> dict[str, Any]:
    value = parent.get(key)
    if not isinstance(value, dict):
        report.error(key, "must be an object")
        return {}
    return value


def require_list(parent: dict[str, Any], key: str, report: Report) -> list[Any]:
    value = parent.get(key)
    if not isinstance(value, list):
        report.error(key, "must be an array")
        return []
    return value


def require_text(parent: dict[str, Any], key: str, path: str, report: Report) -> None:
    if not text_value(parent.get(key)):
        report.error(f"{path}.{key}", "must be a non-empty string")


def require_text_list(
    parent: dict[str, Any],
    key: str,
    path: str,
    report: Report,
    minimum: int = 1,
) -> None:
    value = parent.get(key)
    if not isinstance(value, list) or len(value) < minimum:
        report.error(f"{path}.{key}", f"must contain at least {minimum} item(s)")
        return
    for index, item in enumerate(value):
        if not text_value(item):
            report.error(f"{path}.{key}[{index}]", "must be a non-empty string")


def find_forbidden_keys(value: Any, path: str, report: Report) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else key
            if key.lower() in FORBIDDEN_KEYS:
                report.error(child_path, "is outside this content-only Skill")
            find_forbidden_keys(child, child_path, report)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            find_forbidden_keys(child, f"{path}[{index}]", report)


def validate_package(data: dict[str, Any], report: Report) -> str | None:
    package = require_object(data, "package", report)
    require_text(package, "name", "package", report)
    mode = package.get("mode")
    if mode not in MODES:
        report.error("package.mode", f"must be one of {sorted(MODES)}")
        mode = None
    if package.get("region") not in REGIONS:
        report.error("package.region", f"must be one of {sorted(REGIONS)}")
    if package.get("model") not in MODELS:
        report.error("package.model", f"must be one of {sorted(MODELS)}")
    return mode


def validate_product(data: dict[str, Any], report: Report) -> None:
    product = require_object(data, "product", report)
    for key in (
        "name",
        "description",
        "primary_user",
        "use_moment",
        "problem",
        "product_action",
        "visible_result",
    ):
        require_text(product, key, "product", report)

    direction = require_object(data, "content_direction", report)
    for key in ("summary", "tone", "visual_style"):
        require_text(direction, key, "content_direction", report)


def validate_platform_strategy(
    data: dict[str, Any],
    report: Report,
    mode: str | None,
    strict: bool,
) -> None:
    strategy = require_object(data, "platform_strategy", report)
    require_text(strategy, "primary_platform", "platform_strategy", report)
    require_text(strategy, "recommendation_logic", "platform_strategy", report)

    minimum_platforms = 3 if mode == "COMPLETE_PROMOTION_PACKAGE" else 1
    cards = require_list(strategy, "platform_cards", report)
    if len(cards) < minimum_platforms:
        (report.error if strict else report.warn)(
            "platform_strategy.platform_cards",
            f"should contain at least {minimum_platforms} platform recommendation(s)",
        )
    for index, card in enumerate(cards):
        path = f"platform_strategy.platform_cards[{index}]"
        if not isinstance(card, dict):
            report.error(path, "must be an object")
            continue
        for key in (
            "name",
            "priority",
            "market_audience",
            "content_role",
            "best_formats",
            "fit_reason",
            "adaptation_focus",
        ):
            require_text(card, key, path, report)

    require_text_list(
        strategy,
        "not_prioritized",
        "platform_strategy",
        report,
        minimum=1,
    )

    minimum_mappings = 12 if mode == "COMPLETE_PROMOTION_PACKAGE" else 1
    mappings = require_list(strategy, "content_mapping", report)
    if len(mappings) < minimum_mappings:
        (report.error if strict else report.warn)(
            "platform_strategy.content_mapping",
            f"should contain at least {minimum_mappings} content-to-platform mapping(s)",
        )
    for index, mapping in enumerate(mappings):
        path = f"platform_strategy.content_mapping[{index}]"
        if not isinstance(mapping, dict):
            report.error(path, "must be an object")
            continue
        for key in ("source_asset", "primary_platform", "platform_reason", "adaptation_focus"):
            require_text(mapping, key, path, report)

    minimum_adaptations = 12 if mode == "COMPLETE_PROMOTION_PACKAGE" else 1
    adaptations = require_list(strategy, "adaptation_sets", report)
    if len(adaptations) < minimum_adaptations:
        (report.error if strict else report.warn)(
            "platform_strategy.adaptation_sets",
            f"should contain at least {minimum_adaptations} platform-native adaptation(s)",
        )
    for index, adaptation in enumerate(adaptations):
        path = f"platform_strategy.adaptation_sets[{index}]"
        if not isinstance(adaptation, dict):
            report.error(path, "must be an object")
            continue
        for key in (
            "source_asset",
            "platform",
            "audience",
            "format",
            "title_or_hook",
            "structure",
            "native_copy",
            "visual_treatment",
            "product_appearance",
            "ending",
            "key_difference",
        ):
            require_text(adaptation, key, path, report)


def validate_records(
    data: dict[str, Any],
    key: str,
    report: Report,
    required_fields: tuple[str, ...],
    minimum: int,
    strict: bool,
) -> list[dict[str, Any]]:
    records = require_list(data, key, report)
    if len(records) < minimum:
        message = f"should contain at least {minimum} item(s)"
        (report.error if strict else report.warn)(key, message)
    valid_records: list[dict[str, Any]] = []
    for index, record in enumerate(records):
        path = f"{key}[{index}]"
        if not isinstance(record, dict):
            report.error(path, "must be an object")
            continue
        valid_records.append(record)
        for field in required_fields:
            require_text(record, field, path, report)
        require_text_list(record, "assets", path, report)
    return valid_records


def validate_highlights_and_stories(data: dict[str, Any], report: Report, strict: bool) -> None:
    validate_records(
        data,
        "highlights",
        report,
        (
            "name",
            "audience",
            "use_moment",
            "before",
            "product_action",
            "result",
            "image_text_treatment",
            "video_treatment",
        ),
        3,
        strict,
    )
    validate_records(
        data,
        "development_stories",
        report,
        (
            "event",
            "conflict",
            "decision",
            "visible_change",
            "image_text_treatment",
            "video_treatment",
        ),
        4,
        strict,
    )
    validate_records(
        data,
        "case_stories",
        report,
        (
            "type",
            "subject",
            "scenario",
            "before",
            "product_action",
            "result",
            "image_text_treatment",
            "video_treatment",
        ),
        3,
        strict,
    )


def validate_angle_bank(data: dict[str, Any], report: Report, strict: bool) -> None:
    angles = validate_records(
        data,
        "angle_bank",
        report,
        (
            "name",
            "audience",
            "scene",
            "core_content",
            "product_role",
            "key_visual",
            "format",
        ),
        20,
        strict,
    )
    names: set[str] = set()
    for index, angle in enumerate(angles):
        name = angle.get("name")
        if text_value(name):
            if name in names:
                report.warn(f"angle_bank[{index}].name", "duplicates another angle name")
            names.add(name)


def validate_image_text(data: dict[str, Any], report: Report, strict: bool) -> None:
    items = require_list(data, "image_text_assets", report)
    if len(items) < 6:
        (report.error if strict else report.warn)("image_text_assets", "should contain at least 6 items")
    for index, item in enumerate(items):
        path = f"image_text_assets[{index}]"
        if not isinstance(item, dict):
            report.error(path, "must be an object")
            continue
        for key in ("id", "angle", "audience_scene", "cover", "copy", "ending", "derivatives"):
            require_text(item, key, path, report)
        require_text_list(item, "titles", path, report, minimum=3)
        require_text_list(item, "page_sequence", path, report, minimum=5)
        require_text_list(item, "assets", path, report)


def validate_short_video(data: dict[str, Any], report: Report, strict: bool) -> None:
    items = require_list(data, "short_video_assets", report)
    if len(items) < 6:
        (report.error if strict else report.warn)("short_video_assets", "should contain at least 6 items")
    for index, item in enumerate(items):
        path = f"short_video_assets[{index}]"
        if not isinstance(item, dict):
            report.error(path, "must be an object")
            continue
        for key in (
            "id",
            "angle",
            "audience_scene",
            "duration",
            "script",
            "screen_text",
            "ending",
            "cover",
            "caption",
            "derivatives",
        ):
            require_text(item, key, path, report)
        require_text_list(item, "hooks", path, report, minimum=3)
        require_text_list(item, "shots", path, report, minimum=5)
        require_text_list(item, "titles", path, report, minimum=3)
        require_text_list(item, "assets", path, report)


def validate(data: Any, strict: bool = False) -> Report:
    report = Report()
    if not isinstance(data, dict):
        report.error("$", "root must be a JSON object")
        return report

    find_forbidden_keys(data, "", report)
    mode = validate_package(data, report)
    validate_product(data, report)

    if mode in {"COMPLETE_PROMOTION_PACKAGE", "PLATFORM_ADAPTATION_PACKAGE"}:
        validate_platform_strategy(data, report, mode, strict)

    if mode in {"COMPLETE_PROMOTION_PACKAGE", "PRODUCT_STORY_PACKAGE"}:
        validate_highlights_and_stories(data, report, strict)
        validate_angle_bank(data, report, strict)
    if mode in {"COMPLETE_PROMOTION_PACKAGE", "IMAGE_TEXT_PACKAGE"}:
        validate_image_text(data, report, strict)
    if mode in {"COMPLETE_PROMOTION_PACKAGE", "SHORT_VIDEO_PACKAGE"}:
        validate_short_video(data, report, strict)

    inventory = require_list(data, "asset_inventory", report)
    if not inventory:
        report.warn("asset_inventory", "should list the screenshots, recordings, results, and visual assets needed")
    return report


def make_record(fields: tuple[str, ...], prefix: str) -> dict[str, Any]:
    record = {field: f"{prefix} {field}" for field in fields}
    record["assets"] = [f"{prefix} screenshot"]
    return record


def self_test() -> int:
    highlight_fields = (
        "name", "audience", "use_moment", "before", "product_action", "result",
        "image_text_treatment", "video_treatment",
    )
    development_fields = (
        "event", "conflict", "decision", "visible_change", "image_text_treatment", "video_treatment",
    )
    case_fields = (
        "type", "subject", "scenario", "before", "product_action", "result",
        "image_text_treatment", "video_treatment",
    )
    angle_fields = (
        "name", "audience", "scene", "core_content", "product_role", "key_visual", "format",
    )

    valid = {
        "package": {
            "name": "Demo promotion",
            "mode": "COMPLETE_PROMOTION_PACKAGE",
            "region": "DOMESTIC",
            "model": "TOC",
        },
        "product": {
            "name": "Demo",
            "description": "Turns notes into a visual card",
            "primary_user": "Independent creator",
            "use_moment": "After collecting notes",
            "problem": "Notes are hard to present",
            "product_action": "Organizes the notes",
            "visible_result": "A visual card",
        },
        "content_direction": {
            "summary": "Show the transformation",
            "tone": "Clear and direct",
            "visual_style": "Product-first screenshots",
        },
        "platform_strategy": {
            "primary_platform": "Example Platform A",
            "recommendation_logic": "The audience and visible result match the platform format",
            "platform_cards": [
                {
                    "name": f"Example Platform {i}",
                    "priority": "Primary" if i == 0 else "Secondary",
                    "market_audience": "Domestic independent creators",
                    "content_role": "Show a visible product result",
                    "best_formats": "Image sequence and short demo",
                    "fit_reason": "The task and result can be understood visually",
                    "adaptation_focus": "Change the hook, structure, copy, and visual order",
                }
                for i in range(3)
            ],
            "not_prioritized": ["Example Platform D: audience mismatch"],
            "content_mapping": [
                {
                    "source_asset": f"Asset {i}",
                    "primary_platform": f"Example Platform {i % 3}",
                    "platform_reason": "The format matches the asset",
                    "adaptation_focus": "Use a platform-native opening and structure",
                }
                for i in range(12)
            ],
            "adaptation_sets": [
                {
                    "source_asset": f"Asset {i // 3}",
                    "platform": f"Example Platform {i % 3}",
                    "audience": "Independent creator",
                    "format": "Image-text or short video",
                    "title_or_hook": "A platform-native result hook",
                    "structure": "Problem, product action, visible result",
                    "native_copy": "Complete platform-native copy",
                    "visual_treatment": "Reordered screenshots and legible crops",
                    "product_appearance": "Product appears after the problem is clear",
                    "ending": "Natural product summary",
                    "key_difference": "Different hook, structure, copy, and visual order",
                }
                for i in range(12)
            ],
        },
        "highlights": [make_record(highlight_fields, f"highlight {i}") for i in range(3)],
        "development_stories": [make_record(development_fields, f"development {i}") for i in range(4)],
        "case_stories": [make_record(case_fields, f"case {i}") for i in range(3)],
        "angle_bank": [make_record(angle_fields, f"angle {i}") for i in range(20)],
        "image_text_assets": [
            {
                "id": f"I{i}",
                "angle": "Before and after",
                "audience_scene": "After collecting notes",
                "titles": ["Title A", "Title B", "Title C"],
                "cover": "Before and after visual",
                "page_sequence": [f"Page {j}" for j in range(5)],
                "assets": ["input", "output", "screen capture"],
                "copy": "Complete image-text copy",
                "ending": "Product summary",
                "derivatives": "Short image version",
            }
            for i in range(6)
        ],
        "short_video_assets": [
            {
                "id": f"V{i}",
                "angle": "Input to output",
                "audience_scene": "After collecting notes",
                "duration": "30 seconds",
                "hooks": ["Hook A", "Hook B", "Hook C"],
                "script": "Complete narration",
                "shots": [f"Shot {j}" for j in range(5)],
                "screen_text": "Input to visual card",
                "assets": ["input", "output", "screen recording"],
                "ending": "Product summary",
                "cover": "Result visual",
                "titles": ["Title A", "Title B", "Title C"],
                "caption": "Video caption",
                "derivatives": "Silent cut",
            }
            for i in range(6)
        ],
        "asset_inventory": ["product screenshots", "screen recordings", "before and after results"],
    }

    valid_report = validate(valid, strict=True)
    if valid_report.errors:
        for error in valid_report.errors:
            print(f"SELF-TEST ERROR: {error}")
        return 1

    invalid = dict(valid)
    invalid["calendar"] = [{"day": 1}]
    invalid["publishing_schedule"] = [{"time": "tomorrow"}]
    invalid["metrics"] = {"views": 100}
    invalid["conversion"] = {"path": "signup"}
    invalid["experiments"] = [{"variant": "A"}]
    invalid["review"] = {"result": "later"}
    invalid["stop_conditions"] = ["low views"]
    invalid_report = validate(invalid, strict=True)
    required_errors = (
        "calendar",
        "publishing_schedule",
        "metrics",
        "conversion",
        "experiments",
        "review",
        "stop_conditions",
    )
    missing = [key for key in required_errors if not any(key in error for error in invalid_report.errors)]
    if missing:
        for key in missing:
            print(f"SELF-TEST ERROR: forbidden key not rejected: {key}")
        return 1

    print(
        "SELF-TEST PASS: platform recommendations and adaptations accepted; "
        "schedules, metrics, conversion, experiments, review, and stop conditions rejected"
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", nargs="?", type=Path, help="Path to promotion-package JSON")
    parser.add_argument("--strict", action="store_true", help="Treat content minimums as errors")
    parser.add_argument("--self-test", action="store_true", help="Run built-in tests")
    args = parser.parse_args()

    if args.self_test:
        return self_test()
    if args.package is None:
        parser.error("package is required unless --self-test is used")

    try:
        data = json.loads(args.package.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"ERROR: file not found: {args.package}", file=sys.stderr)
        return 2
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: cannot read valid JSON: {exc}", file=sys.stderr)
        return 2

    report = validate(data, strict=args.strict)
    for warning in report.warnings:
        print(f"WARNING: {warning}")
    for error in report.errors:
        print(f"ERROR: {error}")

    if report.errors:
        print(f"FAIL: {len(report.errors)} error(s), {len(report.warnings)} warning(s)")
        return 1
    print(f"PASS: 0 errors, {len(report.warnings)} warning(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
