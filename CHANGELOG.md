# Changelog

All notable changes to the FDA PharmaVigilance project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project setup and documentation
- Project structure for ingestion, dbt, and streamlit layers
- Comprehensive .gitignore for credential protection
- Contributing guidelines
- Security best practices documentation

### Changed
- N/A

### Fixed
- N/A

### Removed
- N/A

## [0.1.0] - 2026-06-03

### Added
- Project initialization
- Git configuration with comprehensive .gitignore
- README files for all layers
- Environment configuration template (.env.example)
- Contributing guidelines
- MIT License
- Changelog

### Features
- Bronze layer placeholder for raw FDA data
- Silver layer transformation documentation
- Gold layer aggregation models
- Streamlit dashboard structure
- Security best practices guide

---

## Semantic Versioning Guide

- **MAJOR**: Breaking changes to data structure or API
- **MINOR**: New features, backward compatible
- **PATCH**: Bug fixes, documentation updates

## Release Process

1. Update version in relevant files
2. Update this CHANGELOG
3. Create git tag: `git tag -a v0.1.0 -m "Release v0.1.0"`
4. Push tag: `git push origin v0.1.0`

## Version History Format

Each entry follows this format:

```
## [version] - YYYY-MM-DD

### Added
- New features

### Changed
- Changes to existing functionality

### Fixed
- Bug fixes

### Removed
- Removed features

### Deprecated
- Features to be removed in future versions

### Security
- Security-related changes
```

---

**Last Updated**: June 3, 2026
