# Architecture

## System Overview

Algorithm Discovery Lab is a modular platform for autonomous algorithm discovery, formal verification, and benchmarking.

```
┌──────────────────────────────┐
│   Discovery Problem          │
│   (SortingNetworkProblem)    │
└──────────┬───────────────────┘
           │
           ▼
┌──────────────────────────────┐
│     Search Engine            │
│  ┌────────────────────────┐  │
│  │ EvolutionarySearch     │  │
│  │ RandomSearch           │  │
│  │ MAPElitesSearch        │  │
│  └────────────────────────┘  │
└──────────┬───────────────────┘
           │
     ┌─────┴─────┐
     ▼           ▼
┌─────────┐ ┌─────────┐
│Candidate│ │Candidate│
│Generator│ │Mutation │
└────┬────┘ └────┬────┘
     └─────┬─────┘
           ▼
┌──────────────────────────────┐
│   Correctness Verifier       │
│  ExhaustiveVerifier          │
│  (SAT/SMT backends later)    │
└──────────┬───────────────────┘
           │
     PASS  │  FAIL
     │     └──→ DISCARD
     ▼
┌──────────────────────────────┐
│   Cost Analysis              │
│   (comparator count, depth)  │
└──────────┬───────────────────┘
           ▼
┌──────────────────────────────┐
│   Benchmarking Engine        │
│   (wall-clock, statistics)   │
└──────────┬───────────────────┘
           ▼
┌──────────────────────────────┐
│   Discovery Archive          │
│   (SQLite + Discovery Museum)│
└──────────┬───────────────────┘
           ▼
┌──────────────────────────────┐
│   Web Dashboard / CLI        │
└──────────────────────────────┘
```

## Key Design Decisions

### Why Sorting Networks First?

Sorting networks are ideal for MVP because:
1. **Exhaustive verification is feasible** for n ≤ 8 (256 inputs max)
2. **Well-studied** — known baselines exist for comparison
3. **Clean metrics** — comparator count and depth are well-defined
4. **Visual** — network structure can be displayed clearly

### Why Separate Verification from Fitness?

The search fitness function is not trusted as proof. A candidate may score well on structural metrics (comparator count, depth) but still fail to sort correctly. The verifier is an independent, formally grounded check.

### Why SQLite?

SQLite requires zero setup, works offline, and handles the expected data volume for individual research runs. PostgreSQL support can be added later via the same Storage interface.

### Why No LLM?

The base system works without any LLM or API. ML-guided search is an optional future extension that improves search efficiency but never determines correctness.

## Module Structure

```
src/algorithm_discovery_lab/
├── core/           # Candidate, Discovery, Problem interfaces
├── search/         # Search strategies (evolutionary, random, MAP-Elites)
├── verification/   # Correctness verifiers (exhaustive, future: SAT/SMT)
├── benchmarking/   # Performance measurement engine
├── problems/       # Problem domains (sorting networks, future: others)
├── experiments/    # Experiment runner orchestration
├── storage/        # SQLite persistence
├── config/         # Configuration management
└── cli/            # Command-line interface
```

## Extensibility

To add a new discovery domain:

1. Implement `DiscoveryProblem` interface
2. Implement candidate representation
3. Implement serialization
4. Implement verifier (at minimum, exhaustive)
5. Register in the CLI and web API

No changes to the search engine, benchmarking engine, or storage are needed.
