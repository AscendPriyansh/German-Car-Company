# test_fleet_report.py
from fleet_report import fleet_summary

SAMPLE = [
    {"id": "VOS-4471", "odometer": 14900, "last_service_km": 0},
    {"id": "VOS-2210", "odometer": 48400, "last_service_km": 45000},
]


def test_summary_counts_due_cars():
    # Only VOS-4471 is nearly worn, so exactly one car is due.
    assert fleet_summary(SAMPLE)["due"] == 1


def test_missing_reading_does_not_crash_report():
    # A car with no last_service_km must not raise a KeyError — the report must complete
    # and include that car in the result without treating it as fully worn.
    fleet = [
        {"id": "VOS-4471", "odometer": 14900, "last_service_km": 0},
        {"id": "VOS-7788", "odometer": 92000},   # no last_service_km
    ]
    summary = fleet_summary(fleet)
    assert "average_wear" in summary, "fleet_summary must return average_wear"
    assert summary["count"] == 2, "both cars must be counted"
    # VOS-7788 has no service record so it must NOT be counted as due
    assert summary["due"] == 1, "only the near-worn car should be flagged"
