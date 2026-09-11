# Security Policy

## Threat Model

Algorithm Discovery Lab executes search-generated candidates internally using Python data structures. The system does NOT execute arbitrary generated source code.

### What is safe

- Sorting network candidates are represented as data (lists of comparator pairs)
- Verification runs on internal Python code, not user-provided scripts
- No shell execution of generated candidates
- No network access by the core system

### Future considerations

If external execution backends are added (e.g., compiling and running generated C code):

- Sandboxed execution with process isolation
- Timeout limits
- Resource limits (memory, CPU)
- Restricted filesystem access
- No network access
- Input validation before execution

## Reporting Vulnerabilities

Open a GitHub issue or contact the maintainers directly.
