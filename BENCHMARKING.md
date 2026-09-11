# Benchmarking Methodology

## Principles

1. **Controlled environment**: Same hardware, same conditions
2. **Statistical rigor**: Multiple trials, report median + stddev
3. **Honest reporting**: Never present single-run results as universal
4. **Context always documented**: CPU, OS, compiler, Python version

## How Benchmarks Work

### For Sorting Networks

1. **Warmup**: 100 iterations to stabilize CPU caches
2. **Measurement**: 1000 repetitions, each with 10 inner trials
3. **Aggregation**: Median of inner trials per repetition
4. **Statistics**: median, mean, stddev, min, max across repetitions

### Input Distribution

- Random integers from uniform distribution [0, 1000]
- Same random seed for all candidates in comparison
- Input length = n (number of wires)

### What We Measure

- **Wall-clock time**: `time.perf_counter_ns()` nanosecond resolution
- **Comparator count**: Abstract structural metric
- **Depth**: Abstract structural metric (critical path length)

### What We Don't Claim

- "Faster on all hardware"
- "Universally better than baseline"
- "Optimal implementation"

Instead we say:
- "Faster on this benchmark configuration (AMD Ryzen 9, Python 3.12, Ubuntu 22.04)"
- "X% fewer comparators than baseline"
- "Verified improvement under specified conditions"

## Benchmark Fairness

All candidates in a comparison are benchmarked:
- On the same hardware
- With the same Python version
- With the same random seed for inputs
- With the same warmup and repetition count

## Hardware Context

Every benchmark result includes:
- Platform (OS version)
- Processor model
- Python version
- Timestamp
