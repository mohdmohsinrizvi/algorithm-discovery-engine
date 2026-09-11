# Research Methodology

## Research Question

Can automated search discover formally verified implementations of small deterministic algorithms that outperform established baselines under clearly defined computational constraints?

## Hypotheses

**H1:** Evolutionary search finds valid high-quality sorting networks more efficiently than random search under equal search budgets.

**H2:** Diversity preservation mechanisms improve discovery of structurally different high-quality candidates.

**H3:** Quality-Diversity (MAP-Elites) search discovers a broader range of high-quality solutions than single-objective evolutionary search.

These are hypotheses to be tested, not established facts.

## Methodology

### Experimental Design

Each experiment consists of:

1. **Problem definition**: Sorting network for n wires
2. **Baseline**: Known-good implementation (insertion-sort derived or optimal)
3. **Search configuration**: Algorithm, population, generations, seed
4. **Verification**: Exhaustive binary input testing
5. **Benchmarking**: Controlled microbenchmarks with statistics

### Metrics

**Structural metrics** (abstract):
- Comparator count
- Network depth

**Performance metrics** (hardware-dependent):
- Median execution time (ns)
- Mean, stddev, min, max

**Search metrics**:
- Generations to first verified candidate
- Total candidates evaluated
- Total verified candidates
- Archive coverage (MAP-Elites)

### Reproducibility

Every experiment is defined by:
- Configuration YAML file
- Random seed
- Hardware description
- Software environment

The command `adl reproduce <DISC-ID>` replays the experiment from stored configuration.

### Statistical Rigor

- Multiple seeds per experiment (recommended: ≥10)
- Median + stddev reported, not single runs
- Hardware/software context always documented
- No cherry-picking successful runs

## Threats to Validity

1. **Search may rediscover known solutions** — this is expected, not a failure
2. **Benchmark results are hardware-dependent** — never presented as universal
3. **Exhaustive verification only for n ≤ 8** — larger n requires different methods
4. **Small-domain results may not generalize** — clearly documented
5. **Evolutionary algorithms can converge prematurely** — diversity mechanisms mitigate but don't eliminate this
