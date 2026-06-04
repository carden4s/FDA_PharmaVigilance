# Contributing to FDA PharmaVigilance

Thank you for your interest in contributing! This guide will help you understand how to contribute effectively.

## Code of Conduct

- Be respectful and constructive in all interactions
- Provide helpful feedback on pull requests
- Focus on the code, not the person
- Report issues and concerns to the maintainers

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork**: `git clone https://github.com/YOUR_USERNAME/FDA_PharmaVigilance.git`
3. **Create a feature branch**: `git checkout -b feature/your-feature-name`
4. **Set up your environment**: `pip install -r requirements.txt`
5. **Make your changes**
6. **Test thoroughly**
7. **Push your branch**: `git push origin feature/your-feature-name`
8. **Create a Pull Request** with a clear description

## Development Workflow

### Branch Naming
- `feature/` - New features
- `bugfix/` - Bug fixes
- `hotfix/` - Critical production fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring without functional changes
- `test/` - Test additions or improvements

Example: `feature/fda-api-retry-logic`

### Commit Messages
Follow conventional commit format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Type**: feat, fix, docs, style, refactor, test, chore
**Scope**: ingestion, dbt, streamlit, docs, infra
**Subject**: Concise description (50 chars max)

Examples:
```
feat(ingestion): add FDA API retry mechanism with exponential backoff
fix(dbt): correct sex_code mapping in stg_fda_adverse_events
docs(setup): clarify Snowflake role requirements
```

## Code Standards

### Python Style
- Use PEP 8 formatting
- Run `black` for auto-formatting: `black .`
- Run `flake8` for linting: `flake8 .`
- Use type hints where possible
- Max line length: 100 characters
- Use meaningful variable names

```python
# Good
def fetch_adverse_events(drug_name: str) -> List[dict]:
    """Fetch adverse events for a given drug."""
    pass

# Avoid
def get_data(d):
    return fda_api.get(d)
```

### dbt Standards
- Use `snake_case` for model names
- Prefix staging models with `stg_`
- Prefix fact tables with `fct_`
- Prefix aggregate tables with `agg_`
- Add descriptions to all models and columns
- Include tests for critical models
- Keep SQL readable and well-commented

```yaml
# Example model configuration
models:
  - name: stg_fda_adverse_events
    description: "Cleaned and standardized FDA adverse events"
    columns:
      - name: event_id
        description: "Unique adverse event identifier"
        tests:
          - unique
          - not_null
```

### Streamlit Code
- Organize with functions and sections
- Use meaningful component keys: `st.button("Calculate", key="calc_button")`
- Add docstrings to functions
- Cache expensive operations: `@st.cache_data`
- Handle errors gracefully with try/except

## Testing

### Python Tests
```bash
cd ingestion
pytest tests/
# With coverage
pytest --cov=src tests/
```

### dbt Tests
```bash
cd dbt
dbt test
dbt test -s stg_fda_adverse_events  # Test specific model
```

### Manual Testing
1. Test with sample data locally
2. Test all data pipeline steps end-to-end
3. Verify Streamlit dashboard with test data
4. Check error handling and edge cases

## Pull Request Process

1. **Update documentation** if you change functionality
2. **Add tests** for new features (aim for >80% coverage)
3. **Update CHANGELOG.md** with your changes
4. **Write a clear PR description**:
   - What problem does it solve?
   - How does it solve it?
   - Any breaking changes?
   - Screenshots if UI changes
5. **Link related issues**: "Closes #123"
6. **Request review** from maintainers

### PR Description Template
```markdown
## Description
Brief description of changes

## Problem
What problem does this solve?

## Solution
How does it solve it?

## Testing
How was this tested?

## Checklist
- [ ] Code follows style guidelines
- [ ] Added tests
- [ ] Updated documentation
- [ ] No credentials in commits
- [ ] Checked dbt models (if applicable)
```

## Security Considerations

### Before Committing
- ✅ Use `.env.example` as template
- ✅ Store actual credentials in `.env` (not committed)
- ✅ Run `git diff --cached` to review changes
- ✅ Check for accidentally committed credentials

### Never Commit
- `.env` files with actual credentials
- API keys or tokens
- Database passwords
- Private keys or certificates
- Snowflake connection details

### If You Accidentally Commit Credentials
1. **Immediately** notify the maintainers
2. Rotate all exposed credentials
3. Use `git-filter-repo` to remove from history
4. Force-push only with maintainer approval

## Documentation

### README Updates
- Keep it accurate and current
- Add code examples for new features
- Update architecture diagrams if needed
- Link to detailed docs

### docstrings
All functions should have docstrings:

```python
def calculate_serious_rate(events: List[dict], drug_id: str) -> float:
    """
    Calculate the percentage of serious adverse events for a drug.
    
    Args:
        events: List of adverse event dictionaries
        drug_id: FDA drug ID identifier
        
    Returns:
        Percentage of events marked as serious (0-100)
        
    Raises:
        ValueError: If drug_id not found in events
    """
    pass
```

## Performance Considerations

- Optimize dbt queries for large datasets
- Use Snowflake clustering for common filters
- Cache Streamlit results: `@st.cache_data`
- Profile Python code for bottlenecks
- Monitor query execution times

## Questions?

- Check existing issues and PRs
- Review documentation in `/docs/`
- Ask in PR comments
- Contact maintainers

## Recognition

Contributors will be recognized in:
- GitHub contributors page
- Release notes
- Project documentation

Thank you for contributing! 🙌
