# valk-cron

Cron expressions and a job scheduler for [Valk](https://valk-lang.dev): the next and previous
times of an expression in any time zone, and jobs that run on them in coroutines. Purely written
in Valk.

Requires Valk 0.7.6 or newer.

## Install

```
vman install github.com/ctxcode/valk-cron
```

## Example

```rust
use cron
use valk.time

let schedule = cron.parse("30 9 * * MON-FRI") ! panic(E.message)
let zone = time.zone("Europe/Amsterdam") ! panic("Unknown zone")
let now = time.DateTime.now_in(zone)

let next = schedule.next(now)          // ?DateTime, in the zone of `now`
let prev = schedule.prev(now)
each schedule.upcoming(now) as at, i {
    if i == 5 : break
    println(at)                        // 2026-10-05T09:30:00+02:00 ...
}
if schedule.matches(now) : println("now is a match")
```

`next` returns the first time after the one it is given, `prev` the last time before it, both
`null` when there is none within the years 1 to 9999. Times are whole seconds.

## Scheduler

```rust
use cron
use valk.signal
use valk.sync

fn main() {
    let scheduler = cron.Scheduler.new()   // local time zone; or Scheduler.new(zone)
    scheduler.add("*/5 * * * *", fn() { println("every five minutes") }) ! panic(E.message)
    let backup = scheduler.add("0 3 * * *", fn() { run_backup() }, "backup") ! panic(E.message)
    let at = backup.next_run()
    if isset(at) : println("next backup at " + at)

    let stop: shared sync.CancelToken = sync.CancelToken.new() ! panic("init")
    signal.cancel_on_shutdown(stop) ! panic("signals")
    scheduler.run(stop) ! panic("init")    // returns after Ctrl-C and the running jobs ended
}
```

- Each run starts in a coroutine on the thread that calls `run`, at the time the schedule gives,
  so runs do not drift. A job that does heavy work can start a thread of its own.
- A job whose previous run is still busy skips the run and counts it in `skipped`; set
  `job.overlap = true` to run them side by side.
- `run` stops when the token is cancelled and waits for the runs in progress. Jobs can be added
  and removed while it runs: `scheduler.remove("backup")`, `job.remove()`, `scheduler.get(name)`.
- A run that was missed because the thread was busy or the machine slept runs once, as soon as
  it can; more missed runs of the same job are dropped.

## Expressions

Five fields, `minute hour day-of-month month day-of-week`, or six with `second` in front.

| | |
|---|---|
| `*` | every value |
| `5`, `1,15` | values and lists |
| `9-17`, `FRI-MON`, `22-2` | ranges; a range may wrap around |
| `*/15`, `0-30/10`, `5/15` | steps; `5/15` is `5-59/15` |
| `JAN`-`DEC`, `SUN`-`SAT` | names, in any case; Sunday is `0` or `7` |
| `?` | `*`, in the day fields |
| `L`, `L-3` | the last day of the month, three days before it |
| `15W`, `LW` | the weekday nearest to the 15th within the month, the last weekday |
| `5L` (or `L5`) | the last Friday of the month |
| `MON#2` | the second Monday of the month |
| `@yearly` (`@annually`), `@monthly`, `@weekly`, `@daily` (`@midnight`), `@hourly` | the usual macros |

When both day fields are restricted, a day matches either one, as in Vixie cron:
`0 0 13 * FRI` runs on the 13th and on every Friday. When one of them starts with `*` or is `?`,
a day must match both: `0 0 */2 * MON` runs on odd days that are Mondays.

A bad expression throws `cron.Error` with a message that names the problem:

```
Invalid cron expression "0 24 * * *": hour 24 is out of range 0-23
```

The codes are `syntax`, `range`, `impossible` (no date matches, as `0 0 30 2 *`) and, from
`Scheduler.add`, `exists` (the name is taken).

## Daylight saving time

A schedule matches wall-clock time in the zone of the time it is given.

- A time that the clocks skip does not run: `30 2 * * *` in Europe/Amsterdam has no run on the
  day summer time starts.
- A time that happens twice runs once, at its first occurrence.
- A schedule with `*` in the hour field keeps its pace through a repeated hour: `*/30 * * * *`
  runs at 02:00 and 02:30 in summer time, then again at 02:00 and 02:30 in winter time.

## Benchmarks

Chained `next` calls on an AMD Ryzen 5 7600X (`make bench`), and the same with Python's croniter
(`bench/croniter_bench.py`):

| Expression | UTC | Europe/Amsterdam | croniter (UTC) |
|---|---|---|---|
| `*/5 * * * *` | 98 ns | 130 ns | 16.8 µs |
| `0 9 * * MON-FRI` | 105 ns | 385 ns | 22.9 µs |
| `30 2 L * *` | 129 ns | 416 ns | 33.2 µs |
| `0 0 29 2 *` | 184 ns | 470 ns | 58.4 µs |
| `*/10 * * * * *` | 67 ns | 118 ns | 12.4 µs |

Parsing an expression takes about 0.3 µs.

## Not supported

`@every`, `@reboot`, a seventh field for the year, Quartz's weekday numbers 1-7 (Sunday is 0
here), `L` alone in the day of week, `W` on a range, Jenkins' `H`, and a `CRON_TZ=` prefix (give
the scheduler a zone instead). The scheduler does not catch up on runs from before it started.

## Development

`make test` runs the suite, `make example` runs the example, `make lint` checks the sources,
`make bench` runs the benchmark and `make docs` regenerates the API documentation.
`python3 tests/crosscheck.py` (needs `pip install croniter`) regenerates
`tests/croniter-samples.valk`, the next and previous times of a thousand expressions by croniter.
