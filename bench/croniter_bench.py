# The same measurement with Python's croniter (pip install croniter)
import time
from datetime import datetime
from zoneinfo import ZoneInfo
from croniter import croniter

EXPRESSIONS = ["*/5 * * * *", "0 9 * * MON-FRI", "30 2 L * *", "0 0 * * L5", "0 0 29 2 *", "*/10 * * * * *"]
COUNT = 20_000
for zone in ["UTC", "Europe/Amsterdam"]:
    for expression in EXPRESSIONS:
        start = datetime(2026, 1, 1, tzinfo=ZoneInfo(zone))
        it = croniter(expression, start, second_at_beginning=True)
        started = time.perf_counter_ns()
        for _ in range(COUNT):
            try:
                at = it.get_next(datetime)
            except Exception:
                it = croniter(expression, start, second_at_beginning=True)
        ns = (time.perf_counter_ns() - started) // COUNT
        print(f'{zone} "{expression}": {ns} ns per next, last {at:%Y-%m-%d}')
