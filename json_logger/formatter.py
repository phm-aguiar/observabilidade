"""JSON formatter for Python's standard logging module."""

from __future__ import annotations

import json
import logging
import traceback
from datetime import datetime, timezone
from typing import Any


class JsonFormatter(logging.Formatter):
    """Formata registros de log como objetos JSON.

    Campos padrão emitidos em cada linha:
        timestamp  – ISO-8601 em UTC
        level      – nome do nível (INFO, ERROR, …)
        logger     – nome do logger
        message    – mensagem formatada
        module     – módulo que originou o log
        function   – função que originou o log
        line       – número da linha

    Campos extras passados via ``extra={}`` são mesclados ao objeto raiz.
    Exceções são serializadas no campo ``exception``.

    Exemplo::

        import logging
        from json_logger import JsonFormatter

        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())

        logger = logging.getLogger("meu_app")
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

        logger.info("serviço iniciado", extra={"porta": 8080})
    """

    DEFAULT_FIELDS = (
        "timestamp",
        "level",
        "logger",
        "message",
        "module",
        "function",
        "line",
    )

    # Atributos internos do LogRecord que não devem vazar como campos extras
    _INTERNAL_ATTRS: frozenset[str] = frozenset(
        {
            "args",
            "created",
            "exc_info",
            "exc_text",
            "filename",
            "funcName",
            "levelname",
            "levelno",
            "lineno",
            "message",
            "module",
            "msecs",
            "msg",
            "name",
            "pathname",
            "process",
            "processName",
            "relativeCreated",
            "stack_info",
            "taskName",
            "thread",
            "threadName",
        }
    )

    def __init__(
        self,
        fields: list[str] | None = None,
        timestamp_key: str = "timestamp",
        json_indent: int | None = None,
        json_ensure_ascii: bool = False,
    ) -> None:
        """Inicializa o formatador.

        Args:
            fields: Lista de campos padrão a incluir na saída.
                    Quando ``None`` todos os campos padrão são emitidos.
            timestamp_key: Nome da chave para o timestamp.
            json_indent: Indentação JSON (``None`` = compacto).
            json_ensure_ascii: Passar ``True`` para escapar caracteres não-ASCII.
        """
        super().__init__()
        self.fields = list(fields) if fields is not None else list(self.DEFAULT_FIELDS)
        self.timestamp_key = timestamp_key
        self.json_indent = json_indent
        self.json_ensure_ascii = json_ensure_ascii

    # ------------------------------------------------------------------
    # Implementação principal
    # ------------------------------------------------------------------

    def format(self, record: logging.LogRecord) -> str:
        """Converte um LogRecord em uma string JSON."""
        record.message = record.getMessage()

        log_object: dict[str, Any] = {}

        # Campos padrão selecionados
        field_map = {
            "timestamp": self._get_timestamp(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.message,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        for field in self.fields:
            if field in field_map:
                log_object[field] = field_map[field]

        # Campos extras fornecidos pelo chamador
        for key, value in record.__dict__.items():
            if key not in self._INTERNAL_ATTRS and not key.startswith("_"):
                log_object[key] = value

        # Exceção
        if record.exc_info:
            log_object["exception"] = self._format_exception(record.exc_info)
        elif record.exc_text:
            log_object["exception"] = record.exc_text

        # Stack info
        if record.stack_info:
            log_object["stack_info"] = self.formatStack(record.stack_info)

        return json.dumps(
            log_object,
            indent=self.json_indent,
            ensure_ascii=self.json_ensure_ascii,
            default=str,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _get_timestamp(record: logging.LogRecord) -> str:
        """Retorna o timestamp do registro em ISO-8601 (UTC)."""
        dt = datetime.fromtimestamp(record.created, tz=timezone.utc)
        return dt.isoformat(timespec="milliseconds")

    @staticmethod
    def _format_exception(exc_info: tuple) -> str:
        """Formata informações de exceção como string."""
        return "".join(traceback.format_exception(*exc_info)).rstrip()
