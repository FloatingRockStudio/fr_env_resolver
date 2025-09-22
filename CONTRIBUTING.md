# fr_env_resolver Contribution info

## Testing

```bash
# All tests
rez-env fr_env_resolver python-3.9 pytest -- python -m pytest tests/

# With coverage
rez-env fr_env_resolver python-3.9 pytest pytest_cov -- python -m pytest tests/ --cov=fr_env_resolver
```


## Architecture

fr_env_resolver/
├── __init__.py          # Public API
├── _internal/           # Private API
├── _internal/cli/       # Command line interface implementation
├── _internal/impl/      # Core implementations
├── _internal/core/      # Utilities and validation
├── constants.py         # Constant variables/config
├── exceptions.py        # Custom Exceptions
├── interfaces.py        # Class interface contracts
└── structs.py           # Data structures
```

## Contributing

1. Add tests for new functionality
2. Update docs for API changes
3. Run full test suite before submitting
```


### Code Style

- Follow PEP 8 style guidelines
- Use type hints where possible
- Document public APIs with docstrings
- Keep functions focused and testable
