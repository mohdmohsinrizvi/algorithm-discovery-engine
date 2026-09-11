# Algorithm Discovery Lab

> Autonomous algorithm discovery, formal verification & benchmarking platform

**Search. Verify. Benchmark. Discover.**

## Motivation

Can automated search discover formally verified implementations of small deterministic algorithms that outperform established baselines under clearly defined computational constraints?

This platform implements that question as a working system.

## What It Does

Give the system a computational problem and a baseline, then it automatically:

1. **Searches** through alternative implementations using evolutionary algorithms
2. **Verifies** correctness exhaustively for small input domains
3. **Benchmarks** candidates under controlled conditions with statistical rigor
4. **Discovers** verified candidates as reproducible research artifacts

## Quick Start

```bash
# Clone and install
git clone https://github.com/yourname/algorithm-discovery-lab.git
cd algorithm-discovery-lab
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Run the demo
adl demo

# Run a real experiment
adl discover --n 5 --search evolutionary --population 100 --generations 200 --seed 42

# View discoveries
adl museum
```

## CLI Commands

```bash
adl demo                                          # Quick demo experiment
adl discover --n 8 --search evolutionary          # Run discovery
adl verify candidate.json                         # Verify a candidate
adl benchmark candidate.json                      # Benchmark a candidate
adl museum                                        # View discoveries
adl run experiments/configs/sorting_n8.yaml       # Run from config
adl status                                        # System status
```

## Web Dashboard

```bash
python -m web.server
# Open http://localhost:8000
```

Features:
- Discovery Lab — configure and launch experiments
- Verification Console — verify sorting networks
- Discovery Museum — browse verified discoveries
- Experiments — view past experiment runs

## Architecture

```
Search Engine → Candidate Generator → Correctness Verifier → Cost Analysis → Benchmarking → Discovery Archive
```

- **Search strategies**: Random, Evolutionary, MAP-Elites (Quality-Diversity)
- **Verification**: Exhaustive binary input testing for n ≤ 8
- **Benchmarking**: Controlled microbenchmarks with warmup, multiple trials, statistics
- **Storage**: SQLite (upgradeable to PostgreSQL)
- **Extensibility**: Plugin architecture for new problem domains

See [docs/architecture.md](docs/architecture.md) for details.

## Scientific Principles

- **Correctness is formally verified**, never trusted from the search fitness function
- **Benchmarks report statistics** (median, mean, stddev), not single runs
- **Every discovery includes exact conditions** under which improvement was observed
- **Results are reproducible** from seed + configuration
- **No fake claims** — verified results are labeled VERIFIED, unverified results are labeled UNVERIFIED

## Research Documentation

- [RESEARCH.md](RESEARCH.md) — Research question, hypotheses, methodology
- [REPRODUCIBILITY.md](REPRODUCIBILITY.md) — How to reproduce experiments
- [BENCHMARKING.md](BENCHMARKING.md) — Benchmarking methodology and fairness
- [ARCHITECTURE.md](docs/architecture.md) — System architecture and design decisions

## Limitations

- Search may rediscover known solutions — this is expected, not a failure
- Benchmark results are hardware-dependent — never presented as universal
- Exhaustive verification only for n ≤ 8 — larger n requires different methods
- Small-domain results may not generalize — clearly documented
- Evolutionary algorithms can converge prematurely

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT
