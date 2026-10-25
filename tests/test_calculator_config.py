"""Configuration defaults, precedence, validation, and path resolution."""

import pytest

from app.calculator_config import CalculatorConfig
from app.exceptions import ConfigurationError


def load_config(tmp_path, **kwargs):
    return CalculatorConfig.load(base_dir=tmp_path, environ={}, **kwargs)


def test_defaults_use_project_relative_directories_without_creating_files(tmp_path):
    config = load_config(tmp_path)
    assert config.log_dir == tmp_path / "logs"
    assert config.history_dir == tmp_path / "data"
    assert config.log_file == tmp_path / "logs" / "calculator.log"
    assert config.history_file == tmp_path / "data" / "history.csv"
    assert config.max_history_size == 1000
    assert config.auto_save is False
    assert config.precision == 15
    assert config.max_input_value == 1e308
    assert config.encoding == "utf-8"
    assert config.log_dir.is_dir() and config.history_dir.is_dir()
    assert not config.log_file.exists() and not config.history_file.exists()


def test_env_file_process_and_overrides_precedence(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "CALCULATOR_PRECISION=2\nCALCULATOR_AUTO_SAVE=false\n"
        "CALCULATOR_HISTORY_FILE=file.csv\n", encoding="utf-8",
    )
    config = CalculatorConfig.load(
        base_dir=tmp_path, environ={"CALCULATOR_PRECISION": "3", "CALCULATOR_AUTO_SAVE": "TRUE"},
        overrides={"CALCULATOR_PRECISION": "4"},
    )
    assert config.precision == 4
    assert config.auto_save is True
    assert config.history_file == tmp_path / "data" / "file.csv"


def test_relative_and_absolute_paths_resolve_consistently(tmp_path):
    absolute_log = tmp_path / "elsewhere" / "calc.log"
    config = load_config(tmp_path, overrides={
        "CALCULATOR_LOG_DIR": "custom-logs",
        "CALCULATOR_HISTORY_DIR": "custom-history",
        "CALCULATOR_LOG_FILE": str(absolute_log),
        "CALCULATOR_HISTORY_FILE": "nested/history.csv",
    })
    assert config.log_dir == tmp_path / "custom-logs"
    assert config.log_file == absolute_log
    assert config.history_file == tmp_path / "custom-history" / "nested" / "history.csv"


@pytest.mark.parametrize(
    "name,value",
    [
        ("CALCULATOR_MAX_HISTORY_SIZE", "0"),
        ("CALCULATOR_MAX_HISTORY_SIZE", "1.5"),
        ("CALCULATOR_PRECISION", "-1"),
        ("CALCULATOR_PRECISION", "abc"),
        ("CALCULATOR_MAX_INPUT_VALUE", "0"),
        ("CALCULATOR_MAX_INPUT_VALUE", "-4"),
        ("CALCULATOR_MAX_INPUT_VALUE", "nan"),
        ("CALCULATOR_MAX_INPUT_VALUE", "inf"),
        ("CALCULATOR_AUTO_SAVE", "yes"),
        ("CALCULATOR_DEFAULT_ENCODING", "no-such-encoding"),
        ("CALCULATOR_LOG_DIR", ""),
        ("CALCULATOR_HISTORY_FILE", ""),
    ],
)
def test_invalid_values_raise_configuration_error(tmp_path, name, value):
    with pytest.raises(ConfigurationError, match=name):
        load_config(tmp_path, overrides={name: value})


def test_unknown_override_is_rejected(tmp_path):
    with pytest.raises(ConfigurationError, match="Unknown configuration"):
        load_config(tmp_path, overrides={"NOT_A_SETTING": "value"})


def test_existing_file_cannot_be_used_as_directory(tmp_path):
    (tmp_path / "occupied").write_text("content", encoding="utf-8")
    with pytest.raises(ConfigurationError, match="CALCULATOR_LOG_DIR"):
        load_config(tmp_path, overrides={"CALCULATOR_LOG_DIR": "occupied"})


def test_existing_directory_cannot_be_used_as_file(tmp_path):
    (tmp_path / "logs" / "occupied").mkdir(parents=True)
    with pytest.raises(ConfigurationError, match="CALCULATOR_LOG_FILE"):
        load_config(tmp_path, overrides={"CALCULATOR_LOG_FILE": "occupied"})


def test_env_file_path_must_be_a_file(tmp_path):
    with pytest.raises(ConfigurationError, match="not a file"):
        load_config(tmp_path, env_file=tmp_path)
