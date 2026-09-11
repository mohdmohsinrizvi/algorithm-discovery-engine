# Contributing to Algorithm Discovery Lab

## How to Contribute

### Reporting Bugs

Open a GitHub issue with:
- Description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Python version and OS

### Suggesting Features

Open a GitHub issue with:
- Use case description
- Proposed interface changes
- Scientific justification if applicable

### Adding a New Discovery Domain

1. Create `src/algorithm_discovery_lab/problems/your_domain.py`
2. Implement `DiscoveryProblem` interface
3. Implement candidate representation and serialization
4. Implement verifier
5. Add tests in `tests/unit/test_your_domain.py`
6. Register in CLI and web API

### Adding a New Search Algorithm

1. Create `src/algorithm_discovery_lab/search/your_strategy.py`
2. Implement `SearchStrategy` interface
3. Add tests
4. Register in `experiments/runner.py`

### Adding a New Verifier Backend

1. Create class implementing `Verifier` interface in `verification/verifier.py`
2. Add tests with intentionally incorrect candidates
3. Register in `get_verifier()` factory

## Development Setup

```bash
git clone https://github.com/yourname/algorithm-discovery-lab.git
cd algorithm-discovery-lab
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## Code Style

- Type hints on all public functions
- Docstrings for public APIs
- `ruff` for linting
- `mypy` for type checking

## Testing Requirements

- All new code must have tests
- Verification tests must include intentionally incorrect candidates
- Integration tests for search → verify → benchmark pipeline
- Same seed must produce deterministic results where promised

## Scientific Integrity

- Never fabricate benchmark numbers
- Never claim discovery without verification evidence
- Always document hardware/software context
- Clearly distinguish hypotheses from established facts
