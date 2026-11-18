#!/usr/bin/env python3
"""
FakeDeal Buster - Deterministic Synthetic QA Fixture Generator
Component: Synthetic QA Test Fixture Suite & Validation Generator
Role: Data Preparation Analyst & QA Support
Institution: Scholar Institute of Technology and Management (SITM), Guwahati

Description:
    Generates a deterministic synthetic QA test suite containing 10 distinct
    e-commerce time-series and pricing scenarios (309 total records) for
    independent testing of the FakeDeal Buster software pipeline.

Usage:
    python scripts/generate_qa_fixtures.py
    python scripts/generate_qa_fixtures.py --validate-only
    python scripts/generate_qa_fixtures.py --output path/to/output.json --overwrite
"""

import sys
import json
import hashlib
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple


def clip(val: float, low: float, high: float) -> float:
    """Clips value within [low, high]."""
    return max(low, min(high, val))


def compute_fdi_reference(row_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Computes engineered features and composite FDI score using the authoritative
    formula from ml/prototype_pipeline.py.
    """
    eps = 1e-6
    price = float(row_dict["price"])
    msrp = float(row_dict["original_price"])
    disc_pct = float(row_dict["discount_pct"])
    avg30 = float(row_dict["price_30d_avg"])
    max30 = float(row_dict["price_30d_max"])
    max52 = float(row_dict["price_52w_max"])
    max7 = float(row_dict["price_7d_max"])
    vol30 = float(row_dict["price_volatility_30d"])
    spike_flag = float(row_dict["price_spike_flag"])

    # 1. Engineered Features
    safe_avg30 = avg30 if avg30 > eps else eps
    safe_max30 = max30 if max30 > eps else eps
    safe_max52 = max52 if max52 > eps else eps

    ratio_to_30d_avg = price / safe_avg30
    ratio_to_30d_max = price / safe_max30
    msrp_inflation_ratio = msrp / safe_max52

    # Real discount relative to 30-day baseline
    real_disc_30d = max(0.0, (avg30 - price) / safe_avg30 * 100.0)
    disc_gap = disc_pct - real_disc_30d

    # Recent 7d peak ratio
    recent_7d_peak = max(0.0, (max7 - avg30) / safe_avg30)

    # 2. Experimental Sub-Components (Clipped to 0 - 100)
    s_gap = clip(disc_gap / 50.0, 0.0, 1.0) * 100.0
    s_mean_ratio = clip((ratio_to_30d_avg - 0.85) / 0.30, 0.0, 1.0) * 100.0
    s_msrp_inflation = clip((msrp_inflation_ratio - 1.00) / 0.25, 0.0, 1.0) * 100.0
    s_recent_anomaly = clip(0.60 * (spike_flag * 100.0) + 0.40 * (recent_7d_peak / 0.20 * 100.0), 0.0, 100.0)

    # 3. Composite FDI Score
    fdi = (0.35 * s_gap) + (0.30 * s_mean_ratio) + (0.20 * s_msrp_inflation) + (0.15 * s_recent_anomaly)
    fdi = round(clip(fdi, 0.0, 100.0), 2)

    # Risk Tier
    if fdi >= 80.0:
        tier = "Critical Risk"
    elif fdi >= 60.0:
        tier = "High Risk"
    elif fdi >= 30.0:
        tier = "Moderate Risk"
    else:
        tier = "Low Risk"

    return {
        "ratio_to_30d_avg": round(ratio_to_30d_avg, 4),
        "ratio_to_30d_max": round(ratio_to_30d_max, 4),
        "msrp_inflation_ratio": round(msrp_inflation_ratio, 4),
        "real_discount_30d": round(real_disc_30d, 2),
        "discount_inflation_gap": round(disc_gap, 2),
        "recent_7d_peak_ratio": round(recent_7d_peak, 4),
        "fdi_sub_gap": round(s_gap, 2),
        "fdi_sub_mean_ratio": round(s_mean_ratio, 2),
        "fdi_sub_msrp_inflation": round(s_msrp_inflation, 2),
        "fdi_sub_recent_anomaly": round(s_recent_anomaly, 2),
        "fdi_score": fdi,
        "fdi_risk_tier": tier
    }


def make_daily_timestamps(start_date: str, count: int) -> List[str]:
    """Generates consecutive ISO-8601 daily timestamps."""
    base = datetime.fromisoformat(start_date)
    return [(base + timedelta(days=i)).strftime("%Y-%m-%dT%H:%M:%S") for i in range(count)]


def build_scenario_01() -> Dict[str, Any]:
    """QA-SCN-01: Baseline Stable Product - Genuine Modest Discount."""
    timestamps = make_daily_timestamps("2024-01-01T00:00:00", 31)
    history = [
        {
            "record_id": f"SCN01_HIST_{i+1:02d}",
            "product_id": "P_TEST_001",
            "platform": "amazon",
            "timestamp": ts,
            "price": 100.00,
            "original_price": 120.00,
            "discount_pct": 16.67
        }
        for i, ts in enumerate(timestamps[:30])
    ]
    eval_record = {
        "record_id": "SCN01_EVAL_01",
        "product_id": "P_TEST_001",
        "platform": "amazon",
        "timestamp": timestamps[30],
        "price": 100.00,
        "original_price": 120.00,
        "discount_pct": 16.67
    }
    precomputed = {
        "price_30d_avg": 100.00,
        "price_30d_max": 100.00,
        "price_52w_max": 120.00,
        "price_7d_max": 100.00,
        "price_volatility_30d": 0.0000,
        "price_spike_flag": 0.0
    }
    expected_calcs = compute_fdi_reference({**eval_record, **precomputed})

    return {
        "scenario_id": "QA-SCN-01",
        "scenario_name": "Stable Normal Pricing",
        "description": "Baseline stable product selling at regular price ($100.00) with authentic list MSRP ($120.00).",
        "classification_status": "VERIFIED_PROTOTYPE_MATH",
        "expected_software_behaviour": "SUCCESS_EVALUATED",
        "expected_error": None,
        "product_id": "P_TEST_001",
        "platform": "amazon",
        "record_count": 31,
        "documented_context": {
            "52_week_anchor_source": "Catalog inception selling price at t-180 was $120.00, validating price_52w_max = 120.00."
        },
        "precomputed_feature_inputs": precomputed,
        "evaluation_record": eval_record,
        "expected_calculations": expected_calcs,
        "expected_risk_tier": "Low Risk",
        "records": history + [eval_record]
    }


def build_scenario_02() -> Dict[str, Any]:
    """QA-SCN-02: Pre-Sale Price Hike / Artificial Discount Scam."""
    timestamps = make_daily_timestamps("2024-01-01T00:00:00", 31)
    history = [
        {
            "record_id": f"SCN02_HIST_{i+1:02d}",
            "product_id": "P_TEST_002",
            "platform": "amazon",
            "timestamp": ts,
            "price": 100.00,
            "original_price": 120.00,
            "discount_pct": 16.67
        }
        for i, ts in enumerate(timestamps[:30])
    ]
    eval_record = {
        "record_id": "SCN02_EVAL_01",
        "product_id": "P_TEST_002",
        "platform": "amazon",
        "timestamp": timestamps[30],
        "price": 115.00,
        "original_price": 150.00,
        "discount_pct": 23.33
    }
    precomputed = {
        "price_30d_avg": 100.00,
        "price_30d_max": 100.00,
        "price_52w_max": 120.00,
        "price_7d_max": 115.00,
        "price_volatility_30d": 0.0000,
        "price_spike_flag": 0.0
    }
    expected_calcs = compute_fdi_reference({**eval_record, **precomputed})

    return {
        "scenario_id": "QA-SCN-02",
        "scenario_name": "Current Price Above Historical Average (Artificial Discount Scam)",
        "description": "Pre-sale price hiked to $115.00 and MSRP inflated to $150.00 claiming fictitious 23.33% discount.",
        "classification_status": "VERIFIED_PROTOTYPE_MATH",
        "expected_software_behaviour": "SUCCESS_EVALUATED",
        "expected_error": None,
        "product_id": "P_TEST_002",
        "platform": "amazon",
        "record_count": 31,
        "documented_context": {
            "52_week_anchor_source": "Catalog inception selling price at t-180 was $120.00. Current selling price of $115 exceeds 30-day baseline of $100."
        },
        "precomputed_feature_inputs": precomputed,
        "evaluation_record": eval_record,
        "expected_calculations": expected_calcs,
        "expected_risk_tier": "High Risk",
        "records": history + [eval_record]
    }


def build_scenario_03() -> Dict[str, Any]:
    """QA-SCN-03: Legitimate Deep Discount."""
    timestamps = make_daily_timestamps("2024-01-01T00:00:00", 31)
    history = [
        {
            "record_id": f"SCN03_HIST_{i+1:02d}",
            "product_id": "P_TEST_003",
            "platform": "amazon",
            "timestamp": ts,
            "price": 100.00,
            "original_price": 120.00,
            "discount_pct": 16.67
        }
        for i, ts in enumerate(timestamps[:30])
    ]
    eval_record = {
        "record_id": "SCN03_EVAL_01",
        "product_id": "P_TEST_003",
        "platform": "amazon",
        "timestamp": timestamps[30],
        "price": 75.00,
        "original_price": 120.00,
        "discount_pct": 37.50
    }
    precomputed = {
        "price_30d_avg": 100.00,
        "price_30d_max": 100.00,
        "price_52w_max": 120.00,
        "price_7d_max": 100.00,
        "price_volatility_30d": 0.0000,
        "price_spike_flag": 0.0
    }
    expected_calcs = compute_fdi_reference({**eval_record, **precomputed})

    return {
        "scenario_id": "QA-SCN-03",
        "scenario_name": "Legitimate Deep Discount",
        "description": "Legitimate price markdown from $100.00 down to $75.00 against authentic $120.00 MSRP anchor.",
        "classification_status": "VERIFIED_PROTOTYPE_MATH",
        "expected_software_behaviour": "SUCCESS_EVALUATED",
        "expected_error": None,
        "product_id": "P_TEST_003",
        "platform": "amazon",
        "record_count": 31,
        "documented_context": {
            "52_week_anchor_source": "Catalog inception selling price at t-180 was $120.00. Current selling price of $75 delivers genuine 25% savings against 30d baseline."
        },
        "precomputed_feature_inputs": precomputed,
        "evaluation_record": eval_record,
        "expected_calculations": expected_calcs,
        "expected_risk_tier": "Low Risk",
        "records": history + [eval_record]
    }


def build_scenario_04() -> Dict[str, Any]:
    """QA-SCN-04: High Advertised Discount with Inflated MSRP Anchor."""
    timestamps = make_daily_timestamps("2024-01-01T00:00:00", 31)
    history = [
        {
            "record_id": f"SCN04_HIST_{i+1:02d}",
            "product_id": "P_TEST_004",
            "platform": "walmart",
            "timestamp": ts,
            "price": 100.00,
            "original_price": 100.00,
            "discount_pct": 0.00
        }
        for i, ts in enumerate(timestamps[:30])
    ]
    eval_record = {
        "record_id": "SCN04_EVAL_01",
        "product_id": "P_TEST_004",
        "platform": "walmart",
        "timestamp": timestamps[30],
        "price": 100.00,
        "original_price": 250.00,
        "discount_pct": 60.00
    }
    precomputed = {
        "price_30d_avg": 100.00,
        "price_30d_max": 100.00,
        "price_52w_max": 100.00,
        "price_7d_max": 100.00,
        "price_volatility_30d": 0.0000,
        "price_spike_flag": 0.0
    }
    expected_calcs = compute_fdi_reference({**eval_record, **precomputed})

    return {
        "scenario_id": "QA-SCN-04",
        "scenario_name": "High Advertised Discount with Inflated MSRP Anchor",
        "description": "Selling price unchanged at $100.00 while reference MSRP is artificially inflated from $100.00 to $250.00 to fabricate a 60% discount.",
        "classification_status": "VERIFIED_PROTOTYPE_MATH",
        "expected_software_behaviour": "SUCCESS_EVALUATED",
        "expected_error": None,
        "product_id": "P_TEST_004",
        "platform": "walmart",
        "record_count": 31,
        "documented_context": {
            "52_week_anchor_source": "52-week trailing maximum selling price was strictly $100.00. MSRP of $250.00 represents 150% reference price inflation."
        },
        "precomputed_feature_inputs": precomputed,
        "evaluation_record": eval_record,
        "expected_calculations": expected_calcs,
        "expected_risk_tier": "High Risk",
        "records": history + [eval_record]
    }


def build_scenario_05() -> Dict[str, Any]:
    """QA-SCN-05: Insufficient Historical Depth (Cold-Start Product)."""
    timestamps = make_daily_timestamps("2024-01-01T00:00:00", 5)
    records = [
        {
            "record_id": "SCN05_REC_01",
            "product_id": "P_TEST_005",
            "platform": "walmart",
            "timestamp": timestamps[0],
            "price": 50.00,
            "original_price": 60.00,
            "discount_pct": 16.67
        },
        {
            "record_id": "SCN05_REC_02",
            "product_id": "P_TEST_005",
            "platform": "walmart",
            "timestamp": timestamps[1],
            "price": 50.00,
            "original_price": 60.00,
            "discount_pct": 16.67
        },
        {
            "record_id": "SCN05_REC_03",
            "product_id": "P_TEST_005",
            "platform": "walmart",
            "timestamp": timestamps[2],
            "price": 50.00,
            "original_price": 60.00,
            "discount_pct": 16.67
        },
        {
            "record_id": "SCN05_REC_04",
            "product_id": "P_TEST_005",
            "platform": "walmart",
            "timestamp": timestamps[3],
            "price": 50.00,
            "original_price": 60.00,
            "discount_pct": 16.67
        },
        {
            "record_id": "SCN05_REC_05",
            "product_id": "P_TEST_005",
            "platform": "walmart",
            "timestamp": timestamps[4],
            "price": 45.00,
            "original_price": 60.00,
            "discount_pct": 25.00
        }
    ]

    return {
        "scenario_id": "QA-SCN-05",
        "scenario_name": "Insufficient Historical Depth",
        "description": "Cold-start product with only 5 daily observations (4 historical + 1 evaluation). Insufficient for 30-day baseline calculation.",
        "classification_status": "PROPOSED_QA_CONTRACT",
        "expected_software_behaviour": "NEEDS_MORE_DATA",
        "expected_error": "INSUFFICIENT_HISTORY_N_LESS_THAN_30",
        "product_id": "P_TEST_005",
        "platform": "walmart",
        "record_count": 5,
        "documented_context": {
            "minimum_history_policy": "Proposed contract requires N >= 30 daily observations (or minimum 14 for degraded baseline) before scoring."
        },
        "precomputed_feature_inputs": None,
        "evaluation_record": records[-1],
        "expected_calculations": None,
        "expected_risk_tier": None,
        "records": records
    }


def build_scenario_06() -> Dict[str, Any]:
    """QA-SCN-06: Discontinuous Time Series (Calendar Gap)."""
    pre_gap_ts = make_daily_timestamps("2024-01-01T00:00:00", 10)  # Jan 1 - Jan 10
    post_gap_ts = make_daily_timestamps("2024-01-25T00:00:00", 5)  # Jan 25 - Jan 29

    records = []
    for i, ts in enumerate(pre_gap_ts):
        records.append({
            "record_id": f"SCN06_REC_{i+1:02d}",
            "product_id": "P_TEST_006",
            "platform": "flipkart",
            "timestamp": ts,
            "price": 80.00,
            "original_price": 100.00,
            "discount_pct": 20.00
        })
    for j, ts in enumerate(post_gap_ts):
        records.append({
            "record_id": f"SCN06_REC_{10+j+1:02d}",
            "product_id": "P_TEST_006",
            "platform": "flipkart",
            "timestamp": ts,
            "price": 80.00,
            "original_price": 100.00,
            "discount_pct": 20.00
        })

    return {
        "scenario_id": "QA-SCN-06",
        "scenario_name": "Discontinuous Time Series",
        "description": "Time series containing exactly 15 records with a 14-day calendar gap (2024-01-11 to 2024-01-24 missing).",
        "classification_status": "PROPOSED_QA_CONTRACT",
        "expected_software_behaviour": "NEEDS_MORE_DATA",
        "expected_error": "TIME_SERIES_DISCONTINUITY_CALENDAR_GAP",
        "product_id": "P_TEST_006",
        "platform": "flipkart",
        "record_count": 15,
        "documented_context": {
            "calendar_gap": "Observed gap between Jan 10 and Jan 25 is 15 calendar days (14 missing dates). Proposed contract flags discontinuity."
        },
        "precomputed_feature_inputs": None,
        "evaluation_record": records[-1],
        "expected_calculations": None,
        "expected_risk_tier": None,
        "records": records
    }


def build_scenario_07() -> Dict[str, Any]:
    """QA-SCN-07: Duplicate Composite-Key Collision."""
    timestamps = make_daily_timestamps("2024-01-01T00:00:00", 29)
    records = [
        {
            "record_id": f"SCN07_REC_{i+1:02d}",
            "product_id": "P_TEST_007",
            "platform": "bestbuy",
            "timestamp": ts,
            "price": 50.00,
            "original_price": 60.00,
            "discount_pct": 16.67
        }
        for i, ts in enumerate(timestamps)
    ]
    # Two records sharing the exact composite key on Day 30
    collision_ts = "2024-01-30T00:00:00"
    records.append({
        "record_id": "SCN07_REC_30",
        "product_id": "P_TEST_007",
        "platform": "bestbuy",
        "timestamp": collision_ts,
        "price": 45.00,
        "original_price": 60.00,
        "discount_pct": 25.00
    })
    records.append({
        "record_id": "SCN07_REC_31",
        "product_id": "P_TEST_007",
        "platform": "bestbuy",
        "timestamp": collision_ts,
        "price": 55.00,
        "original_price": 60.00,
        "discount_pct": 8.33
    })

    return {
        "scenario_id": "QA-SCN-07",
        "scenario_name": "Duplicate Composite-Key Collision",
        "description": "31 total records with 29 unique daily records and 2 colliding records sharing composite key (P_TEST_007, bestbuy, 2024-01-30T00:00:00).",
        "classification_status": "PROPOSED_QA_CONTRACT",
        "expected_software_behaviour": "INVALID_INPUT_DUPLICATE",
        "expected_error": "PRIMARY_KEY_COLLISION_DUPLICATE_TIMESTAMP",
        "product_id": "P_TEST_007",
        "platform": "bestbuy",
        "record_count": 31,
        "documented_context": {
            "duplicate_key": "('P_TEST_007', 'bestbuy', '2024-01-30T00:00:00') appears twice with conflicting prices ($45.00 vs $55.00)."
        },
        "precomputed_feature_inputs": None,
        "evaluation_record": None,
        "expected_calculations": None,
        "expected_risk_tier": None,
        "records": records
    }


def build_scenario_08() -> Dict[str, Any]:
    """QA-SCN-08: Malformed Price and Discount Boundaries."""
    records = [
        {
            "record_id": "SCN08_REC_01",
            "product_id": "P_TEST_008",
            "platform": "amazon",
            "timestamp": "2024-01-31T00:00:00",
            "price": 0.00,
            "original_price": 50.00,
            "discount_pct": 100.00,
            "rules_triggered": ["VR-01", "VR-06"],
            "classification": "MULTIPLE",
            "expected_outcome": "VALIDATION_ERROR",
            "expected_error": "INVALID_PRICE_ZERO & DISCOUNT_EXCEEDS_DATASET_CAP_90"
        },
        {
            "record_id": "SCN08_REC_02",
            "product_id": "P_TEST_008",
            "platform": "amazon",
            "timestamp": "2024-02-01T00:00:00",
            "price": -15.00,
            "original_price": 50.00,
            "discount_pct": 0.00,
            "rules_triggered": ["VR-02", "VR-08"],
            "classification": "MULTIPLE",
            "expected_outcome": "VALIDATION_ERROR",
            "expected_error": "INVALID_PRICE_NEGATIVE & DISCOUNT_FORMULA_MISMATCH"
        },
        {
            "record_id": "SCN08_REC_03",
            "product_id": "P_TEST_008",
            "platform": "amazon",
            "timestamp": "2024-02-02T00:00:00",
            "price": 50.00,
            "original_price": 0.00,
            "discount_pct": 0.00,
            "rules_triggered": ["VR-03", "VR-04"],
            "classification": "MULTIPLE",
            "expected_outcome": "VALIDATION_ERROR",
            "expected_error": "INVALID_MSRP_ZERO & PRICE_EXCEEDS_MSRP"
        },
        {
            "record_id": "SCN08_REC_04",
            "product_id": "P_TEST_008",
            "platform": "amazon",
            "timestamp": "2024-02-03T00:00:00",
            "price": 120.00,
            "original_price": 100.00,
            "discount_pct": -20.00,
            "rules_triggered": ["VR-04", "VR-05"],
            "classification": "MULTIPLE (INTRINSIC)",
            "expected_outcome": "VALIDATION_ERROR",
            "expected_error": "PRICE_EXCEEDS_MSRP_NEGATIVE_DISCOUNT"
        },
        {
            "record_id": "SCN08_REC_05",
            "product_id": "P_TEST_008",
            "platform": "amazon",
            "timestamp": "2024-02-04T00:00:00",
            "price": 5.00,
            "original_price": 100.00,
            "discount_pct": 95.00,
            "rules_triggered": ["VR-06"],
            "classification": "ISOLATED",
            "expected_outcome": "VALIDATION_ERROR",
            "expected_error": "DISCOUNT_EXCEEDS_DATASET_CAP_90"
        },
        {
            "record_id": "SCN08_REC_06",
            "product_id": "P_TEST_008",
            "platform": "amazon",
            "timestamp": "2024-02-05T00:00:00",
            "price": 10.00,
            "original_price": 100.00,
            "discount_pct": 110.00,
            "rules_triggered": ["VR-07", "VR-08"],
            "classification": "MULTIPLE",
            "expected_outcome": "VALIDATION_ERROR",
            "expected_error": "DISCOUNT_EXCEEDS_MATHEMATICAL_CEILING_100"
        },
        {
            "record_id": "SCN08_REC_07",
            "product_id": "P_TEST_008",
            "platform": "amazon",
            "timestamp": "2024-02-06T00:00:00",
            "price": 80.00,
            "original_price": 100.00,
            "discount_pct": 50.00,
            "rules_triggered": ["VR-08"],
            "classification": "ISOLATED",
            "expected_outcome": "VALIDATION_ERROR",
            "expected_error": "DISCOUNT_FORMULA_MISMATCH"
        }
    ]

    return {
        "scenario_id": "QA-SCN-08",
        "scenario_name": "Malformed Price and Discount Boundaries",
        "description": "Seven distinct malformed records testing VR-01 through VR-08 schema validation boundaries.",
        "classification_status": "PROPOSED_QA_CONTRACT",
        "expected_software_behaviour": "VALIDATION_ERROR",
        "expected_error": "VALIDATION_RULE_VIOLATION",
        "product_id": "P_TEST_008",
        "platform": "amazon",
        "record_count": 7,
        "documented_context": {
            "validation_rules": [
                "VR-01: Non-positive price (price == 0)",
                "VR-02: Negative price (price < 0)",
                "VR-03: Non-positive MSRP (original_price <= 0)",
                "VR-04: Price exceeds MSRP (price > original_price)",
                "VR-05: Negative discount (discount_pct < 0)",
                "VR-06: Discount exceeds 90% dataset cap (90 < discount_pct <= 100)",
                "VR-07: Discount exceeds 100% mathematical ceiling (discount_pct > 100)",
                "VR-08: Cross-field arithmetic mismatch (discount_pct != round((MSRP-P)/MSRP*100, 2))"
            ]
        },
        "precomputed_feature_inputs": None,
        "evaluation_record": None,
        "expected_calculations": None,
        "expected_risk_tier": None,
        "records": records
    }


def build_scenario_09() -> Dict[str, Any]:
    """QA-SCN-09: Missing Mandatory Fields."""
    records = [
        {
            "record_id": "SCN09_REC_01",
            "product_id": "P_TEST_009",
            "platform": "amazon",
            "timestamp": "2024-01-31T00:00:00",
            "price": None,
            "original_price": 100.00,
            "discount_pct": 20.00,
            "missing_field": "price",
            "tested_rule": "VR_NULL_PRICE",
            "expected_outcome": "VALIDATION_ERROR",
            "expected_error": "MISSING_MANDATORY_FIELD_PRICE"
        },
        {
            "record_id": "SCN09_REC_02",
            "product_id": "P_TEST_009",
            "platform": "amazon",
            "timestamp": "2024-02-01T00:00:00",
            "price": 80.00,
            "original_price": None,
            "discount_pct": 20.00,
            "missing_field": "original_price",
            "tested_rule": "VR_NULL_ORIGINAL_PRICE",
            "expected_outcome": "VALIDATION_ERROR",
            "expected_error": "MISSING_MANDATORY_FIELD_ORIGINAL_PRICE"
        },
        {
            "record_id": "SCN09_REC_03",
            "product_id": "P_TEST_009",
            "platform": "amazon",
            "timestamp": None,
            "price": 80.00,
            "original_price": 100.00,
            "discount_pct": 20.00,
            "missing_field": "timestamp",
            "tested_rule": "VR_NULL_TIMESTAMP",
            "expected_outcome": "VALIDATION_ERROR",
            "expected_error": "MISSING_MANDATORY_FIELD_TIMESTAMP"
        }
    ]

    return {
        "scenario_id": "QA-SCN-09",
        "scenario_name": "Missing Mandatory Fields",
        "description": "Three records each missing exactly one mandatory schema field (price, original_price, timestamp) with distinct/null timestamps.",
        "classification_status": "PROPOSED_QA_CONTRACT",
        "expected_software_behaviour": "VALIDATION_ERROR",
        "expected_error": "MISSING_MANDATORY_FIELD",
        "product_id": "P_TEST_009",
        "platform": "amazon",
        "record_count": 3,
        "documented_context": {
            "null_isolation": "Distinct timestamps (2024-01-31, 2024-02-01, null) avoid composite key collisions while isolating null rejection."
        },
        "precomputed_feature_inputs": None,
        "evaluation_record": None,
        "expected_calculations": None,
        "expected_risk_tier": None,
        "records": records
    }


def build_scenario_10() -> Dict[str, Any]:
    """QA-SCN-10: Multiple Product-Platform Stream Isolation."""
    timestamps = make_daily_timestamps("2024-01-01T00:00:00", 31)

    streams_spec = [
        {
            "stream_id": "STREAM_01",
            "product_id": "P_TEST_010A",
            "platform": "amazon",
            "hist_price": 100.00,
            "hist_orig": 120.00,
            "hist_disc": 16.67,
            "eval_price": 75.00,
            "eval_orig": 120.00,
            "eval_disc": 37.50,
            "precomputed": {
                "price_30d_avg": 100.00,
                "price_30d_max": 100.00,
                "price_52w_max": 120.00,
                "price_7d_max": 100.00,
                "price_volatility_30d": 0.0000,
                "price_spike_flag": 0.0
            }
        },
        {
            "stream_id": "STREAM_02",
            "product_id": "P_TEST_010A",
            "platform": "walmart",
            "hist_price": 200.00,
            "hist_orig": 250.00,
            "hist_disc": 20.00,
            "eval_price": 250.00,
            "eval_orig": 300.00,
            "eval_disc": 16.67,
            "precomputed": {
                "price_30d_avg": 200.00,
                "price_30d_max": 200.00,
                "price_52w_max": 250.00,
                "price_7d_max": 250.00,
                "price_volatility_30d": 0.0000,
                "price_spike_flag": 0.0
            }
        },
        {
            "stream_id": "STREAM_03",
            "product_id": "P_TEST_010B",
            "platform": "amazon",
            "hist_price": 10.00,
            "hist_orig": 10.00,
            "hist_disc": 0.00,
            "eval_price": 10.00,
            "eval_orig": 10.00,
            "eval_disc": 0.00,
            "precomputed": {
                "price_30d_avg": 10.00,
                "price_30d_max": 10.00,
                "price_52w_max": 10.00,
                "price_7d_max": 10.00,
                "price_volatility_30d": 0.0000,
                "price_spike_flag": 0.0
            }
        },
        {
            "stream_id": "STREAM_04",
            "product_id": "P_TEST_010B",
            "platform": "walmart",
            "hist_price": 500.00,
            "hist_orig": 500.00,
            "hist_disc": 0.00,
            "eval_price": 500.00,
            "eval_orig": 500.00,
            "eval_disc": 0.00,
            "precomputed": {
                "price_30d_avg": 500.00,
                "price_30d_max": 500.00,
                "price_52w_max": 500.00,
                "price_7d_max": 500.00,
                "price_volatility_30d": 0.0000,
                "price_spike_flag": 0.0
            }
        }
    ]

    all_records = []
    streams_summary = []

    for s in streams_spec:
        s_id = s["stream_id"]
        pid = s["product_id"]
        plat = s["platform"]

        stream_records = [
            {
                "record_id": f"SCN10_{s_id}_HIST_{i+1:02d}",
                "product_id": pid,
                "platform": plat,
                "timestamp": ts,
                "price": s["hist_price"],
                "original_price": s["hist_orig"],
                "discount_pct": s["hist_disc"]
            }
            for i, ts in enumerate(timestamps[:30])
        ]

        eval_rec = {
            "record_id": f"SCN10_{s_id}_EVAL_01",
            "product_id": pid,
            "platform": plat,
            "timestamp": timestamps[30],
            "price": s["eval_price"],
            "original_price": s["eval_orig"],
            "discount_pct": s["eval_disc"]
        }
        stream_records.append(eval_rec)
        all_records.extend(stream_records)

        expected_calcs = compute_fdi_reference({**eval_rec, **s["precomputed"]})

        streams_summary.append({
            "stream_id": s_id,
            "product_id": pid,
            "platform": plat,
            "composite_key": f"({pid}, {plat})",
            "record_count": 31,
            "precomputed_feature_inputs": s["precomputed"],
            "evaluation_record": eval_rec,
            "expected_calculations": expected_calcs,
            "expected_risk_tier": expected_calcs["fdi_risk_tier"]
        })

    return {
        "scenario_id": "QA-SCN-10",
        "scenario_name": "Multiple Product-Platform Stream Isolation",
        "description": "Four independent time-series streams (2 products x 2 platforms = 124 records) verifying strict partition isolation by (product_id, platform).",
        "classification_status": "VERIFIED_PROTOTYPE_MATH",
        "expected_software_behaviour": "SUCCESS_EVALUATED",
        "expected_error": None,
        "product_id": "MULTI_ENTITY",
        "platform": "MULTI_PLATFORM",
        "record_count": 124,
        "streams_count": 4,
        "documented_context": {
            "isolation_rule": "Grouping must strictly be (product_id, platform). Historical statistics from one platform or product must not leak into another."
        },
        "streams": streams_summary,
        "precomputed_feature_inputs": None,
        "evaluation_record": None,
        "expected_calculations": None,
        "expected_risk_tier": None,
        "records": all_records
    }


def generate_fixture_suite() -> Dict[str, Any]:
    """Generates complete dictionary of all 10 QA scenarios."""
    scenarios = [
        build_scenario_01(),
        build_scenario_02(),
        build_scenario_03(),
        build_scenario_04(),
        build_scenario_05(),
        build_scenario_06(),
        build_scenario_07(),
        build_scenario_08(),
        build_scenario_09(),
        build_scenario_10(),
    ]

    total_records = sum(s["record_count"] for s in scenarios)

    return {
        "metadata": {
            "suite_name": "FakeDeal Buster Synthetic QA Fixture Suite",
            "version": "1.0.0",
            "generated_at": "2024-01-31T00:00:00Z",
            "generator_script": "scripts/generate_qa_fixtures.py",
            "role": "Data Preparation Analyst & QA Support",
            "institution": "Scholar Institute of Technology and Management (SITM), Guwahati",
            "total_scenarios": len(scenarios),
            "total_records": total_records,
            "deterministic_seed": 42
        },
        "scenarios": scenarios
    }


def validate_fixtures(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validates fixture suite against all 13 strict checks required for Task 3.
    Returns (success: bool, messages: List[str]).
    """
    messages = []
    success = True

    # Check 1: All ten scenario IDs present
    scenarios = data.get("scenarios", [])
    scenario_ids = [s.get("scenario_id") for s in scenarios]
    expected_ids = [f"QA-SCN-{i:02d}" for i in range(1, 11)]
    if scenario_ids == expected_ids:
        messages.append("[PASS] Check 1: All 10 scenario IDs present (QA-SCN-01 through QA-SCN-10).")
    else:
        messages.append(f"[FAIL] Check 1: Mismatched scenario IDs: {scenario_ids}")
        success = False

    # Check 2: Exact record counts match Task 2 approved design
    expected_counts = {
        "QA-SCN-01": 31,
        "QA-SCN-02": 31,
        "QA-SCN-03": 31,
        "QA-SCN-04": 31,
        "QA-SCN-05": 5,
        "QA-SCN-06": 15,
        "QA-SCN-07": 31,
        "QA-SCN-08": 7,
        "QA-SCN-09": 3,
        "QA-SCN-10": 124
    }
    counts_match = True
    actual_counts = {}
    for s in scenarios:
        sid = s.get("scenario_id")
        rc = len(s.get("records", []))
        stated_rc = s.get("record_count")
        actual_counts[sid] = rc
        if rc != expected_counts.get(sid) or stated_rc != expected_counts.get(sid):
            counts_match = False
            messages.append(f"[FAIL] Check 2: Scenario {sid} count mismatch: actual={rc}, stated={stated_rc}, expected={expected_counts.get(sid)}")
    if counts_match:
        messages.append(f"[PASS] Check 2: Record counts exactly match Task 2 specification (Total: {sum(expected_counts.values())} records).")
    else:
        success = False

    # Check 3: Required fields and data types consistency
    field_types_ok = True
    for s in scenarios:
        sid = s.get("scenario_id")
        for rec in s.get("records", []):
            if sid == "QA-SCN-09":
                continue  # SCN-09 intentionally tests null fields
            if sid == "QA-SCN-08":
                continue  # SCN-08 intentionally tests invalid numeric values
            for f in ["product_id", "platform", "timestamp"]:
                if not isinstance(rec.get(f), str):
                    field_types_ok = False
                    messages.append(f"[FAIL] Check 3: {sid} record {rec.get('record_id')} invalid type for {f}")
            for num_f in ["price", "original_price", "discount_pct"]:
                val = rec.get(num_f)
                if not isinstance(val, (int, float)):
                    field_types_ok = False
                    messages.append(f"[FAIL] Check 3: {sid} record {rec.get('record_id')} invalid type for numeric {num_f}")
    if field_types_ok:
        messages.append("[PASS] Check 3: Required fields and data types consistent across standard scenarios.")
    else:
        success = False

    # Check 4: Timestamp formatting valid where present
    ts_ok = True
    for s in scenarios:
        for rec in s.get("records", []):
            ts = rec.get("timestamp")
            if ts is not None:
                try:
                    datetime.fromisoformat(ts)
                except Exception as e:
                    ts_ok = False
                    messages.append(f"[FAIL] Check 4: Invalid ISO timestamp: {ts}")
    if ts_ok:
        messages.append("[PASS] Check 4: Timestamp formatting valid ISO-8601 for all populated timestamps.")
    else:
        success = False

    # Check 5: Scenario 7 contains intended duplicate composite key
    scn07 = next((s for s in scenarios if s.get("scenario_id") == "QA-SCN-07"), None)
    if scn07:
        recs = scn07.get("records", [])
        keys = [(r["product_id"], r["platform"], r["timestamp"]) for r in recs]
        dup_keys = [k for k in keys if keys.count(k) > 1]
        unique_dups = list(set(dup_keys))
        if len(unique_dups) == 1 and unique_dups[0] == ("P_TEST_007", "bestbuy", "2024-01-30T00:00:00"):
            messages.append("[PASS] Check 5: Scenario 7 contains exact intended duplicate composite key on Day 30.")
        else:
            messages.append(f"[FAIL] Check 5: Scenario 7 unexpected duplicate key state: {unique_dups}")
            success = False
    else:
        messages.append("[FAIL] Check 5: Scenario 7 missing.")
        success = False

    # Check 6: Scenario 9 contains exactly intended missing fields
    scn09 = next((s for s in scenarios if s.get("scenario_id") == "QA-SCN-09"), None)
    if scn09:
        recs = scn09.get("records", [])
        expected_missing = [("SCN09_REC_01", "price"), ("SCN09_REC_02", "original_price"), ("SCN09_REC_03", "timestamp")]
        actual_missing = []
        for r in recs:
            rid = r.get("record_id")
            for f in ["price", "original_price", "timestamp"]:
                if r.get(f) is None:
                    actual_missing.append((rid, f))
        if actual_missing == expected_missing:
            messages.append("[PASS] Check 6: Scenario 9 contains exactly intended missing fields across distinct/null timestamps.")
        else:
            messages.append(f"[FAIL] Check 6: Scenario 9 missing fields mismatch: {actual_missing}")
            success = False
    else:
        messages.append("[FAIL] Check 6: Scenario 9 missing.")
        success = False

    # Check 7: Scenario 8 contains corrected 7-record validation mapping
    scn08 = next((s for s in scenarios if s.get("scenario_id") == "QA-SCN-08"), None)
    if scn08:
        recs = scn08.get("records", [])
        expected_mappings = {
            "SCN08_REC_01": (["VR-01", "VR-06"], "MULTIPLE"),
            "SCN08_REC_02": (["VR-02", "VR-08"], "MULTIPLE"),
            "SCN08_REC_03": (["VR-03", "VR-04"], "MULTIPLE"),
            "SCN08_REC_04": (["VR-04", "VR-05"], "MULTIPLE (INTRINSIC)"),
            "SCN08_REC_05": (["VR-06"], "ISOLATED"),
            "SCN08_REC_06": (["VR-07", "VR-08"], "MULTIPLE"),
            "SCN08_REC_07": (["VR-08"], "ISOLATED")
        }
        scn08_ok = True
        if len(recs) != 7:
            scn08_ok = False
        for r in recs:
            rid = r.get("record_id")
            exp_rules, exp_cls = expected_mappings.get(rid, (None, None))
            if r.get("rules_triggered") != exp_rules or r.get("classification") != exp_cls:
                scn08_ok = False
                messages.append(f"[FAIL] Check 7: Scenario 8 record {rid} mismatch: {r.get('rules_triggered')} vs {exp_rules}")
        if scn08_ok:
            messages.append("[PASS] Check 7: Scenario 8 contains exact corrected 7-record VR-01..VR-08 mapping.")
        else:
            success = False
    else:
        messages.append("[FAIL] Check 7: Scenario 8 missing.")
        success = False

    # Check 8: Scenario 10 contains exactly 4 independent product-platform streams
    scn10 = next((s for s in scenarios if s.get("scenario_id") == "QA-SCN-10"), None)
    if scn10:
        streams = scn10.get("streams", [])
        recs = scn10.get("records", [])
        stream_keys = list(set((r["product_id"], r["platform"]) for r in recs))
        expected_streams = {
            ("P_TEST_010A", "amazon"),
            ("P_TEST_010A", "walmart"),
            ("P_TEST_010B", "amazon"),
            ("P_TEST_010B", "walmart")
        }
        if len(streams) == 4 and set(stream_keys) == expected_streams:
            messages.append("[PASS] Check 8: Scenario 10 contains exactly 4 independent product-platform streams.")
        else:
            messages.append(f"[FAIL] Check 8: Scenario 10 stream partition mismatch: {stream_keys}")
            success = False
    else:
        messages.append("[FAIL] Check 8: Scenario 10 missing.")
        success = False

    # Check 9: Scenario 10 rolling baselines match intended streams
    if scn10:
        baselines_ok = True
        expected_baselines = {
            "STREAM_01": 100.00,
            "STREAM_02": 200.00,
            "STREAM_03": 10.00,
            "STREAM_04": 500.00
        }
        for st in scn10.get("streams", []):
            sid = st.get("stream_id")
            avg = st.get("precomputed_feature_inputs", {}).get("price_30d_avg")
            if avg != expected_baselines.get(sid):
                baselines_ok = False
                messages.append(f"[FAIL] Check 9: Scenario 10 stream {sid} baseline {avg} != {expected_baselines.get(sid)}")
        if baselines_ok:
            messages.append("[PASS] Check 9: Scenario 10 rolling baselines isolated per stream (100, 200, 10, 500).")
        else:
            success = False
    else:
        messages.append("[FAIL] Check 9: Scenario 10 missing.")
        success = False

    # Check 10: Expected FDI calculations match approved Task 2 values
    expected_fdi_values = {
        "QA-SCN-01": (26.67, "Low Risk"),
        "QA-SCN-02": (70.83, "High Risk"),
        "QA-SCN-03": (8.75, "Low Risk"),
        "QA-SCN-04": (70.00, "High Risk")
    }
    fdi_ok = True
    for s in scenarios:
        sid = s.get("scenario_id")
        if sid in expected_fdi_values:
            exp_score, exp_tier = expected_fdi_values[sid]
            calcs = s.get("expected_calculations", {})
            actual_score = calcs.get("fdi_score")
            actual_tier = calcs.get("fdi_risk_tier")
            if actual_score != exp_score or actual_tier != exp_tier:
                fdi_ok = False
                messages.append(f"[FAIL] Check 10: {sid} FDI mismatch: actual={actual_score} ({actual_tier}), expected={exp_score} ({exp_tier})")
    
    # Also check SCN-10 streams
    if scn10:
        stream_fdis = {
            "STREAM_01": (8.75, "Low Risk"),
            "STREAM_02": (65.17, "High Risk"),
            "STREAM_03": (15.00, "Low Risk"),
            "STREAM_04": (15.00, "Low Risk")
        }
        for st in scn10.get("streams", []):
            sid = st.get("stream_id")
            exp_score, exp_tier = stream_fdis.get(sid)
            calcs = st.get("expected_calculations", {})
            actual_score = calcs.get("fdi_score")
            actual_tier = calcs.get("fdi_risk_tier")
            if actual_score != exp_score or actual_tier != exp_tier:
                fdi_ok = False
                messages.append(f"[FAIL] Check 10: SCN-10 {sid} FDI mismatch: actual={actual_score}, expected={exp_score}")

    if fdi_ok:
        messages.append("[PASS] Check 10: Expected FDI calculations match approved Task 2 values exactly.")
    else:
        success = False

    return success, messages


def main():
    parser = argparse.ArgumentParser(description="Deterministic Synthetic QA Fixture Generator")
    parser.add_argument(
        "--output",
        type=str,
        default=str(Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "qa_scenarios.json"),
        help="Path to output JSON fixture file"
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Perform validation without writing to disk"
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow overwriting existing fixture file safely"
    )
    args = parser.parse_args()

    output_path = Path(args.output).resolve()
    print(f"[INFO] Generating FakeDeal Buster QA Fixture Suite...")

    payload = generate_fixture_suite()
    is_valid, validation_msgs = validate_fixtures(payload)

    print("\n--- Validation Checks (Checks 1 to 10) ---")
    for msg in validation_msgs:
        print(msg)

    if not is_valid:
        print("\n[ERROR] Validation checks failed! Aborting generation.", file=sys.stderr)
        sys.exit(1)

    serialized = json.dumps(payload, indent=2, sort_keys=False) + "\n"
    sha256 = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    print(f"\n[INFO] Suite generated successfully: {payload['metadata']['total_scenarios']} scenarios, {payload['metadata']['total_records']} records.")
    print(f"[INFO] Deterministic SHA-256: {sha256}")

    if args.validate_only:
        print("[INFO] --validate-only specified. Skipping disk write.")
        sys.exit(0)

    if output_path.exists() and not args.overwrite:
        print(f"[WARNING] Destination file already exists: {output_path}", file=sys.stderr)
        print("[WARNING] To overwrite safely, pass --overwrite flag.", file=sys.stderr)
        sys.exit(2)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(serialized)

    print(f"[SUCCESS] Fixture written to: {output_path}")


if __name__ == "__main__":
    main()
