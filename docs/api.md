
# Documentation

Namespaces: [main](#main)

---

# main

## Errors for 'main'

```js
// Thrown for a cron expression that cannot be used, and by `Scheduler.add`.
+ error Error (syntax, range, impossible, exists) payload { message: String }
```

## Functions for 'main'

```js
// Parses a cron expression.
+ fn parse(expression: String) Schedule !Error
```

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

```js
// The times a schedule matches after a start, from `Schedule.upcoming`, for `each`.
+ class Upcoming {
    // Returns the next time; throws `end` after the last one before the year 10000.
    + fn _next(index: uint) DateTime !IterError
}
```
