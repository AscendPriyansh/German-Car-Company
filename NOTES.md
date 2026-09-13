# What I checked, and what the agent got wrong

## What the agent got wrong

Two things needed a second look before I accepted the output.

First, the missing-reading fix in `needs_service`. The original code defaulted `last_service_km`
to `0` when the key was absent, which sounds harmless until you realise it means every km on the
odometer is counted as km since the last service. A car sitting at 92 000 km with no recorded
service date would show 613% wear and get flagged immediately. The fix I accepted treats a missing
reading as "freshly serviced at the current odometer", so km-since-service is 0 and the car is
not flagged. That is the conservative and correct choice: if we have no data, we do not cry wolf.

Second, I caught that the same defensive default also needed to be applied in `fleet_report.car_wear`,
not just in `km_wachter.needs_service`. The original `car_wear` used `car["last_service_km"]` with
a plain bracket lookup, so it would still raise a `KeyError` even after `needs_service` was fixed.
Both call sites needed the same `.get()` treatment.

## What I checked before I accepted its work

After the fixes were applied I ran `python verify.py` and confirmed all 11 checks pass.

To verify the wear-percentage fix specifically I ran:

```
python -c "from km_wachter import wear_percent; print(wear_percent(14900, 15000))"
```

which prints `99.33...`, not `0`. I also confirmed `SERVICE_INTERVAL_KM` is still 15000 and
`WARN_AT_PERCENT` is still 80 by reading `km_wachter.py` directly — neither constant was touched.
For `settings.cfg` I checked it has not changed from `service_interval_km = 15000` and
`warn_at_percent = 80`. The verify script checks these too, and both pass.

For the miles conversion I ran:

```
python -c "from fleet_utils import km_to_miles; print(km_to_miles(100))"
```

which now prints `62.1371`, within the expected 61–63.5 range. The old value was 160.9 — the
constant had the km-per-mile factor (1.609) where it needed the miles-per-km factor (0.621371).
Every distance sent to the UK partner garage since 2015 was 2.59 times too large.

For the average-wear fix I confirmed the test fleet of two cars (14900 km and 3000 km, both
starting at 0) produces an average of ~59.67%, matching the verify check.

## What the data actually said

The surprising finding was what **did not** predict breakdowns.

The obvious guess would be total odometer reading or vehicle age. Intuitively an older car with
more total kilometres should be closer to failure. The data flatly disagrees. Cars that broke
down averaged 53 448 km total; cars that did not broke averaged 53 302 km — a gap of 146 km
across 120 vehicles, which is noise. Age is even worse: both groups sit at almost exactly 5.9
years. Neither column goes into the risk score.

What **does** predict breakdown is how overdue the car is for its next service right now.
`km_since_service` has a correlation of 0.40 with breakdown — by far the strongest signal.
Cars that broke down averaged 11 678 km since their last service; healthy cars averaged 7 261 km.
That 4 400 km gap is real and consistent.

`avg_daily_km` (how hard the car is driven each day, r = 0.25) and `load_factor` (how heavily
loaded it runs, r = 0.22) both add independent signal. High usage and heavy load push a car
toward breakdown even controlling for service lag.

The risk score combines those three columns, weighted by their correlation strength and
normalised to a 0–100 scale. As a rough validation: the top 25% by risk score broke down at a
53% rate; the bottom 75% broke down at only 11%. The score separates the groups clearly.

The practical takeaway for the fleet team: stop sorting the service queue by odometer. Sort by
km_since_service instead, and give extra priority to cars that also show a high daily-km or
load_factor reading.
