.PHONY: test coverage clean lint \
        validate-requirements validate-tdd validate-implementation validate-verify

test:
	pytest

coverage:
	pytest --cov=swiss-cheese --cov-report=json --cov-report=html:coverage

lint:
	ruff check .

clean:
	rm -rf .coverage htmlcov coverage .pytest_cache .swiss-cheese

# Swiss Cheese Gate Targets (4-layer model)
# Exit 0 = PASS, non-zero = FAIL

validate-requirements:
	@test -f design.md || test -f design.toml || (echo "ERROR: design.md or design.toml required" && exit 1)

validate-tdd:
	@echo "TDD validation - checking tests exist and compile"
	@test -d swiss-cheese/tests || (echo "ERROR: tests directory missing" && exit 1)

validate-implementation:
	@echo "Implementation validation - running tests"
	@pytest -q

validate-verify:
	@echo "Verify - static analysis + coverage"
	@ruff check . --quiet || exit 1
	@pytest --cov=swiss-cheese -q
