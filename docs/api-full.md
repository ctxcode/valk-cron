
# Documentation

Namespaces: [main](#main)

---

# main

## Errors for 'main'

```js
// Thrown for a cron expression that cannot be used, and by `Scheduler.add`.
+ error Error (syntax, range, impossible, exists) payload { message: String }
```

### Error

Thrown for a cron expression that cannot be used, and by `Scheduler.add`.

- `syntax`: the text is not a cron expression: a wrong number of fields, an unknown name or
  macro, or a character that does not belong.
- `range`: a value is outside its field, such as hour `24` or step `0`.
- `impossible`: the expression reads, but no date ever matches it, such as `0 0 30 2 *`.
- `exists`: `Scheduler.add` was given a name that another job already has.

`message` says what is wrong and quotes the expression.

## Functions for 'main'

```js
// Parses a cron expression.
+ fn parse(expression: String) Schedule !Error
```

### parse

Parses a cron expression.

Five fields are `minute hour day-of-month month day-of-week`; six put `second` first. A field
is a list of items split by `,`: `*`, a value, a range `1-5`, and either with a step,
`*/15` or `0-30/10`; `5/15` means `5-59/15`. Months and weekdays also take names (`JAN`,
`MON`), weekdays run from 0 (Sunday) to 7 (Sunday again), and a range may wrap around, as in
`FRI-MON`. `?` is `*` for the day fields.

The day of the month also takes `L` (the last day), `L-3` (three days before it), `15W` (the
weekday nearest to the 15th, within the month) and `LW` (the last weekday). The day of the
week takes `5L` or `L5` (the last Friday) and `MON#2` (the second Monday).

When both day fields are restricted a day matches either one, as in Vixie cron; when one
of them starts with `*` or is `?`, a day must match both. The macros `@yearly`
(`@annually`), `@monthly`, `@weekly`, `@daily` (`@midnight`) and `@hourly` stand for their
usual expressions.

Throws `syntax` or `range` with a message that names the problem, and `impossible` for an
expression no date can match, such as `0 0 30 2 *`.

## Classes for 'main'

```js
// A job of a `Scheduler`, from `Scheduler.add`.
+ class Job {
    // The name given to `add`, or an empty string.
    ~ name: String
    // Whether a run may start while the previous one is still busy. Off by default: such a run is skipped and counted in `skipped`.
    + overlap: bool
    // How many runs have started.
    ~ runs: uint
    // The schedule the job runs on.
    ~ schedule: Schedule
    // How many runs were skipped because the previous one was still busy.
    ~ skipped: uint

    // Returns whether a run of the job is in progress.
    + fn is_running() bool
    // Returns when the job runs next, in the scheduler's zone; `null` once it was removed or its schedule has no more times.
    + fn next_run() ?DateTime
    // Removes the job from its scheduler. A run in progress finishes.
    + fn remove() void
}
```

### Job

A job of a `Scheduler`, from `Scheduler.add`.

#### name

The name given to `add`, or an empty string.

#### overlap

Whether a run may start while the previous one is still busy. Off by default: such a
run is skipped and counted in `skipped`.

#### runs

How many runs have started.

#### schedule

The schedule the job runs on.

#### skipped

How many runs were skipped because the previous one was still busy.

#### is_running

Returns whether a run of the job is in progress.

#### next_run

Returns when the job runs next, in the scheduler's zone; `null` once it was removed or
its schedule has no more times.

#### remove

Removes the job from its scheduler. A run in progress finishes.

```js
// A parsed cron expression: the times it matches, and the next and previous ones.
+ class Schedule {
    // The expression the schedule was parsed from.
    ~+ expression: String

    // Returns whether the wall-clock time of `at`, to the second, matches the schedule.
    + fn matches(at: DateTime) bool
    // Returns the first time after `after` that the schedule matches, in the zone of `after`.
    + fn next(after: DateTime) ?DateTime
    // Returns the last time before `before` that the schedule matches, in the zone of `before`.
    + fn prev(before: DateTime) ?DateTime
    // Returns the times after `after`, in order, for `each`. They run up to the year 9999, so `break` out.
    + fn upcoming(after: DateTime) Upcoming
}
```

### Schedule

A parsed cron expression: the times it matches, and the next and previous ones.

Make one with `cron.parse`. A schedule matches wall-clock times, so `next` and `prev` work in
the time zone of the `DateTime` they are given:

```valk
let schedule = cron.parse("30 9 * * MON-FRI") ! panic(E.message)
let zone = time.zone("Europe/Amsterdam") ! panic("no zone")
let at = schedule.next(time.DateTime.now_in(zone))
```

Around daylight saving changes a time that the clocks skip does not run, and a time that
happens twice runs once, at its first occurrence. A schedule that runs every hour (`*` in
the hour field) keeps running at its minutes through both passes of a repeated hour.

#### expression

The expression the schedule was parsed from.

#### matches

Returns whether the wall-clock time of `at`, to the second, matches the schedule.

#### next

Returns the first time after `after` that the schedule matches, in the zone of `after`.

Times are whole seconds; `null` when there is none before the year 10000.

#### prev

Returns the last time before `before` that the schedule matches, in the zone of `before`.

`null` when there is none after the year 1.

#### upcoming

Returns the times after `after`, in order, for `each`. They run up to the year 9999, so
`break` out.

```valk
each schedule.upcoming(time.DateTime.now()) as at, i {
    if i == 5 : break
    println(at)
}
```

```js
// Runs jobs on cron schedules, each run in a coroutine on the thread that calls `run`.
+ class Scheduler {
    // The zone the schedules are read in.
    ~ zone: Zone

    // Adds a job that calls `callback` at the times of `expression` (see `cron.parse`).
    + fn add(expression: String, callback: fn()(), name: String ("")) Job !Error
    // Returns the job called `name`, or `null`.
    + fn get(name: String) ?Job
    // Returns a scheduler that reads its schedules in `zone`, by default `time.local_zone()`.
    + static fn new(zone: ?Zone (null)) Scheduler
    // Removes the job called `name`; returns false when there is none. A run in progress finishes.
    + fn remove(name: String) bool
    // Runs the jobs until `stop` is cancelled, then waits for the runs in progress to finish.
    + fn run(stop: shared CancelToken) void !sync:SyncError
}
```

### Scheduler

Runs jobs on cron schedules, each run in a coroutine on the thread that calls `run`.

```valk
let scheduler = cron.Scheduler.new()
scheduler.add("*/5 * * * *", fn() { println("every five minutes") }) ! panic(E.message)
let stop: shared sync.CancelToken = sync.CancelToken.new() ! panic("init")
scheduler.run(stop) ! panic("init")
```

Times follow the scheduler's zone, the local one unless another is given. Each run is
due at a time the schedule gives, not a fixed interval after the previous run, so the runs
do not drift. A job whose previous run is still busy when it is due again skips that run,
unless its `overlap` is set. Use a scheduler from one thread; a job that does heavy work
can start a thread of its own.

#### zone

The zone the schedules are read in.

#### add

Adds a job that calls `callback` at the times of `expression` (see `cron.parse`).

Jobs can be added before and while the scheduler runs. A `name` lets `remove` and `get`
find the job; throws `exists` when another job has it, and the errors of `parse`.

#### get

Returns the job called `name`, or `null`.

#### new

Returns a scheduler that reads its schedules in `zone`, by default `time.local_zone()`.

#### remove

Removes the job called `name`; returns false when there is none. A run in progress
finishes.

#### run

Runs the jobs until `stop` is cancelled, then waits for the runs in progress to finish.

Called from a coroutine it only suspends that coroutine; called outside one it runs the
thread's coroutines until it returns. A job whose time is missed, because the thread
was busy or asleep, runs once as soon as it can. Throws `init` when the scheduler's
wake-up channel cannot be made.

```js
// The times a schedule matches after a start, from `Schedule.upcoming`, for `each`.
+ class Upcoming {
    // Returns the next time; throws `end` after the last one before the year 10000.
    + fn _next(index: uint) DateTime !IterError
}
```

### Upcoming

The times a schedule matches after a start, from `Schedule.upcoming`, for `each`.

#### _next

Returns the next time; throws `end` after the last one before the year 10000.
