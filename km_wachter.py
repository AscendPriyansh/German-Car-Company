# km_wachter.py
# KM-Waechter decides when a Vossberg Mobility car needs a service.
# Written in 2013. Modernised 2024.

SERVICE_INTERVAL_KM = 15000
WARN_AT_PERCENT = 80


def wear_percent(km_since_service: float, interval: float) -> float:
    """Return how much of the service interval has been used, as a percentage."""
    ratio = km_since_service / interval   # standard division — keeps the fraction
    return ratio * 100


def needs_service(car: dict) -> bool:
    """Return True when the car has reached or exceeded the warning threshold."""
    last = car.get("last_service_km")
    if last is None:
        # No recorded service reading — treat the car as freshly serviced so it is
        # not falsely flagged.
        last = car["odometer"]
    km_since = car["odometer"] - last
    pct = wear_percent(km_since, SERVICE_INTERVAL_KM)
    return pct >= WARN_AT_PERCENT


def check_fleet(fleet: list) -> list:
    """Flag every car that needs service and return their IDs."""
    flagged = []
    for car in fleet:
        if needs_service(car):
            flagged.append(car["id"])
            print(f"SERVICE DUE: {car['id']}")
    return flagged
