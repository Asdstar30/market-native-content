"""Test helpers: locate the repo, import scripts by path, run script mains."""

from __future__ import annotations

import importlib.util
import io
import sys
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from types import ModuleType

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "skills" / "market-native-core" / "scripts"
EXAMPLE_LIB = REPO / "examples" / "maple-dental" / "market-content-library"
FIXTURES = REPO / "tests" / "fixtures"

if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def load_script(name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def run(module: ModuleType, argv: list[str]) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = module.main(argv)
    return code, out.getvalue(), err.getvalue()
