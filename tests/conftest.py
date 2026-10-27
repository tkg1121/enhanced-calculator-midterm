"""Release test-created log file handles between cases."""

import logging

import pytest


@pytest.fixture(autouse=True)
def close_calculator_log_handlers():
    yield
    for candidate in tuple(logging.Logger.manager.loggerDict.values()):
        if isinstance(candidate, logging.Logger) and candidate.name.startswith("enhanced_calculator."):
            for handler in tuple(candidate.handlers):
                candidate.removeHandler(handler)
                handler.close()
