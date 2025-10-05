# Contributing to Bioprocess Twin

Thank you for your interest in contributing to Bioprocess Twin! This document provides guidelines for contributing to the project.

## Code of Conduct

Be respectful, inclusive, and professional. This is a research project aimed at advancing open-source bioprocess engineering tools.

## How to Contribute

### Reporting Bugs

1. Check [existing issues](https://github.com/yourorg/bioprocess-twin/issues) to avoid duplicates
2. Use the bug report template
3. Include:
   - Hardware/software versions
   - Steps to reproduce
   - Expected vs. actual behavior
   - Log files (sanitize any sensitive data)

### Suggesting Features

1. Check roadmap in README.md (Phase 1/2/3)
2. Open a discussion in [GitHub Discussions](https://github.com/yourorg/bioprocess-twin/discussions)
3. For Phase 1 features, demonstrate alignment with success criteria (MRE ≤ 8%, system uptime ≥ 95%, etc.)

### Pull Requests

#### Before Submitting

1. **Fork** the repository
2. Create a **feature branch** from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. Make your changes following coding standards (see below)
4. **Test** your changes:
   ```bash
   pytest tests/
   ```
5. Update documentation if needed

#### PR Guidelines

- Write clear, concise commit messages (use conventional commits)
- Reference related issues (#123)
- Include tests for new functionality
- Update CHANGELOG.md under `[Unreleased]`
- Ensure CI/CD checks pass (GitHub Actions)

#### Example Commit Message

```
feat(sensor-drivers): add Modbus support for integrated off-gas analyzer

- Implement Modbus RTU driver for BlueSens BlueInOne FERM
- Add auto-fallback from custom CO2/O2 sensors if drift >0.2%
- Update hardware/datasheets/ with wiring diagram

Closes #42
```

## Coding Standards

### Python
- **Style**: PEP 8 (use `black` formatter, `flake8` linter)
- **Docstrings**: Google style
- **Type hints**: Required for all public functions
- **Example**:
  ```python
  def calculate_cer(
      flow_in: float,
      y_co2_out: float,
      pressure: float,
      volume: float
  ) -> float:
      """Calculate Carbon Evolution Rate with pressure correction.

      Args:
          flow_in: Inlet gas flow (L/h)
          y_co2_out: CO2 mole fraction in exhaust (dimensionless)
          pressure: Reactor headspace pressure (bar)
          volume: Reactor working volume (L)

      Returns:
          CER in mol CO2/L/h
      """
      P_std = 1.013  # bar
      return (flow_in * y_co2_out * pressure / P_std) / volume
  ```

### TypeScript (React)
- **Style**: Prettier + ESLint
- **Components**: Functional components with hooks
- **Props**: Use TypeScript interfaces

### Docker
- Multi-stage builds for production images
- Non-root user in final stage
- Explicit versioning (no `latest` tags in production)

### SQL
- Snake_case for table/column names
- Foreign keys with `ON DELETE CASCADE` where appropriate
- Include comments for complex queries

## Development Workflow

### Local Setup

1. **Clone your fork**:
   ```bash
   git clone https://github.com/your-username/bioprocess-twin.git
   cd bioprocess-twin
   ```

2. **Set up Python environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r workstation/requirements.txt
   pip install -r edge/services/digital-twin/requirements.txt
   ```

3. **Start edge stack** (if testing hardware integration):
   ```bash
   cd edge
   cp .env.example .env
   # Edit .env with your configuration
   docker-compose up -d
   ```

### Testing

Run tests before submitting PR:

```bash
# Unit tests
pytest tests/ -v

# Integration tests (requires Docker)
pytest tests/test_mqtt_pipeline.py --docker

# Linting
black .
flake8 .
```

### Sensor Driver Development

If contributing a new sensor driver:

1. Place in `hardware/sensor-drivers/`
2. Follow naming: `{sensor_type}_{interface}_mqtt.py` (e.g., `pressure_modbus_mqtt.py`)
3. Publish to MQTT topic: `bioprocess/pichia/vessel1/sensors/{tag}`
4. Include calibration validation function
5. Add datasheet to `hardware/datasheets/`
6. Update `docs/technical-plan.md` sensor list

### Documentation Updates

- Planning docs (`docs/`) are **authoritative** - changes here may require code updates
- Use markdown for all documentation
- Include diagrams (PNG, SVG) in `docs/architecture/`
- SOPs must be executable by new operators without ambiguity

## Review Process

1. Maintainers review PRs within 1 week
2. Feedback addressed via new commits (don't force-push)
3. Squash merge to `main` after approval
4. Deployment to edge triggered automatically (if CI passes)

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Questions?

- Open a [Discussion](https://github.com/yourorg/bioprocess-twin/discussions)
- Email: your.email@example.com

---

**Thank you for contributing to open bioprocess engineering!**
