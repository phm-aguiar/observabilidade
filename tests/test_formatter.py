"""Testes para json_logger.JsonFormatter."""

import json
import logging

import pytest

from json_logger import JsonFormatter


@pytest.fixture()
def logger(tmp_path):
    """Logger isolado com JsonFormatter e StreamHandler em memória."""
    import io

    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JsonFormatter())

    log = logging.getLogger(f"test_logger_{id(stream)}")
    log.setLevel(logging.DEBUG)
    log.propagate = False
    log.addHandler(handler)

    yield log, stream

    log.removeHandler(handler)


def _last_record(stream) -> dict:
    """Retorna o último registro JSON emitido no stream."""
    stream.seek(0)
    lines = [line for line in stream.read().splitlines() if line.strip()]
    return json.loads(lines[-1])


class TestJsonFormatterDefaultFields:
    def test_emits_valid_json(self, logger):
        log, stream = logger
        log.info("olá mundo")
        record = _last_record(stream)
        assert isinstance(record, dict)

    def test_level_field(self, logger):
        log, stream = logger
        log.warning("atenção")
        record = _last_record(stream)
        assert record["level"] == "WARNING"

    def test_message_field(self, logger):
        log, stream = logger
        log.info("mensagem de teste")
        record = _last_record(stream)
        assert record["message"] == "mensagem de teste"

    def test_logger_field(self, logger):
        log, stream = logger
        log.info("msg")
        record = _last_record(stream)
        assert record["logger"] == log.name

    def test_timestamp_is_iso8601(self, logger):
        from datetime import datetime

        log, stream = logger
        log.info("ts")
        record = _last_record(stream)
        # deve parsear sem exceção
        dt = datetime.fromisoformat(record["timestamp"])
        assert dt.tzinfo is not None  # deve ser timezone-aware

    def test_module_function_line_present(self, logger):
        log, stream = logger
        log.info("campos")
        record = _last_record(stream)
        assert "module" in record
        assert "function" in record
        assert isinstance(record["line"], int)


class TestJsonFormatterExtraFields:
    def test_extra_fields_merged(self, logger):
        log, stream = logger
        log.info("com extra", extra={"porta": 8080, "ambiente": "prod"})
        record = _last_record(stream)
        assert record["porta"] == 8080
        assert record["ambiente"] == "prod"

    def test_extra_does_not_leak_internal_attrs(self, logger):
        log, stream = logger
        log.info("interno")
        record = _last_record(stream)
        # Atributos internos do LogRecord não devem aparecer
        for internal in ("args", "exc_info", "exc_text", "msecs", "levelno"):
            assert internal not in record


class TestJsonFormatterExceptions:
    def test_exception_field_on_error(self, logger):
        log, stream = logger
        try:
            raise ValueError("algo errado")
        except ValueError:
            log.exception("erro capturado")
        record = _last_record(stream)
        assert "exception" in record
        assert "ValueError" in record["exception"]

    def test_no_exception_field_without_error(self, logger):
        log, stream = logger
        log.info("sem erro")
        record = _last_record(stream)
        assert "exception" not in record


class TestJsonFormatterCustomization:
    def test_custom_fields_subset(self):
        import io

        stream = io.StringIO()
        formatter = JsonFormatter(fields=["timestamp", "level", "message"])
        handler = logging.StreamHandler(stream)
        handler.setFormatter(formatter)

        log = logging.getLogger("test_custom_fields")
        log.setLevel(logging.DEBUG)
        log.propagate = False
        log.addHandler(handler)

        log.info("apenas alguns campos")

        stream.seek(0)
        record = json.loads(stream.read().strip())

        assert set(record.keys()) == {"timestamp", "level", "message"}
        log.removeHandler(handler)

    def test_json_indent(self):
        import io

        stream = io.StringIO()
        formatter = JsonFormatter(json_indent=2)
        handler = logging.StreamHandler(stream)
        handler.setFormatter(formatter)

        log = logging.getLogger("test_indent")
        log.setLevel(logging.DEBUG)
        log.propagate = False
        log.addHandler(handler)

        log.info("indentado")

        stream.seek(0)
        output = stream.read()
        # JSON indentado deve ter quebras de linha
        assert "\n" in output
        log.removeHandler(handler)
