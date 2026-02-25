# observabilidade

Biblioteca Python para estruturar logs em **JSON**.

## Instalação

```bash
pip install -e ".[dev]"   # modo desenvolvimento (inclui pytest e ruff)
```

## Uso rápido

```python
import logging
from json_logger import JsonFormatter

handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())

logger = logging.getLogger("meu_app")
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

logger.info("serviço iniciado", extra={"porta": 8080})
# Saída:
# {"timestamp": "2024-01-01T00:00:00.000+00:00", "level": "INFO", "logger": "meu_app",
#  "message": "serviço iniciado", "module": "...", "function": "...", "line": 9, "porta": 8080}
```

## Campos padrão

| Campo       | Descrição                          |
|-------------|------------------------------------|
| `timestamp` | ISO-8601 em UTC                    |
| `level`     | Nível do log (INFO, ERROR, …)      |
| `logger`    | Nome do logger                     |
| `message`   | Mensagem formatada                 |
| `module`    | Módulo de origem                   |
| `function`  | Função de origem                   |
| `line`      | Número da linha                    |

Campos extras passados via `extra={}` são mesclados ao objeto raiz.  
Exceções são serializadas no campo `exception`.

## Personalização

```python
# Apenas alguns campos
formatter = JsonFormatter(fields=["timestamp", "level", "message"])

# Saída indentada (útil para debug)
formatter = JsonFormatter(json_indent=2)
```

## Desenvolvimento

```bash
# Testes
pytest

# Lint
ruff check json_logger/ tests/
```
