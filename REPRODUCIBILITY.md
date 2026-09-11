# Reproducibility Guide

## How to Reproduce an Experiment

Every experiment in Algorithm Discovery Lab is reproducible from stored configuration and random seed.

### From CLI

```bash
# List discoveries
adl museum

# Run from config file
adl run experiments/configs/sorting_n8.yaml

# Demo
adl demo
```

### From Configuration

Each experiment is defined by:

```yaml
problem:
  type: sorting_network
  n: 8

search:
  algorithm: evolutionary
  population_size: 200
  generations: 500
  mutation_rate: 0.15
  crossover_rate: 0.7
  elitism_rate: 0.05

seed: 42
```

The same seed + same configuration = same search trajectory (within the same hardware/Python version).

### Reproducibility Guarantees

- **Deterministic search**: Same seed produces same random sequence
- **Exhaustive verification**: Deterministic for given input space
- **Benchmarking**: Hardware-dependent; reported as context, not universal truth

### What May Vary

- Wall-clock execution time (hardware-dependent)
- Floating-point arithmetic on different architectures
- Python version differences in random number generation

## Recording Reproducibility Context

Every discovery stores:
- Complete search configuration
- Random seed
- Python version
- Platform/processor
- Timestamp

## Extending Reproducibility

To add a new experiment type:

1. Create config YAML
2. Implement `DiscoveryProblem` interface
3. Ensure `generate_random_candidate`, `mutate`, `crossover` use the provided RNG
4. Store results via `Storage`
