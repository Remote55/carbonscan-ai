"""A drop migration's downgrade has to rebuild what was there.

Written from the original by hand, 0004's downgrade got three things wrong on
the first attempt: it called the column `status` when 0001 named it
`payment_status`, dropped its CHECK constraint, and invented index names
(`idx_transactions_buyer`) that 0001 never used (`idx_tx_buyer`). None of that
shows up until someone actually runs `alembic downgrade`, which is the worst
possible moment to find out.

These compare the drop migrations against the schema that created the tables,
by reading the migration source. It is a static check and does not prove the
SQL executes — that needs a live Postgres and belongs in CI — but it does catch
a downgrade that has drifted from the thing it claims to restore.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

VERSIONS = Path(__file__).resolve().parent.parent / "alembic" / "versions"
INITIAL = VERSIONS / "0001_initial_schema.py"


def _create_table_calls(source: str, function: str | None = None) -> dict[str, ast.Call]:
    """Every op.create_table(...) in the file, or in one function, by table name."""
    tree = ast.parse(source)
    scope: ast.AST = tree
    if function is not None:
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == function:
                scope = node
                break
        else:
            raise AssertionError(f"no function named {function}")

    found: dict[str, ast.Call] = {}
    for node in ast.walk(scope):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "create_table"
            and node.args
            and isinstance(node.args[0], ast.Constant)
        ):
            found[node.args[0].value] = node
    return found


def _column_names(call: ast.Call) -> set[str]:
    names = set()
    for arg in call.args[1:]:
        if (
            isinstance(arg, ast.Call)
            and isinstance(arg.func, ast.Attribute)
            and arg.func.attr == "Column"
            and arg.args
            and isinstance(arg.args[0], ast.Constant)
        ):
            names.add(arg.args[0].value)
    return names


def _constraint_names(call: ast.Call) -> set[str]:
    names = set()
    for arg in call.args[1:]:
        if (
            isinstance(arg, ast.Call)
            and isinstance(arg.func, ast.Attribute)
            and arg.func.attr == "CheckConstraint"
        ):
            for keyword in arg.keywords:
                if keyword.arg == "name" and isinstance(keyword.value, ast.Constant):
                    names.add(keyword.value.value)
    return names


def _index_names(source: str, function: str, table: str) -> set[str]:
    """create_index("name", "table", ...) inside one function."""
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == function:
            scope = node
            break
    else:
        raise AssertionError(f"no function named {function}")

    names = set()
    for node in ast.walk(scope):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "create_index"
            and len(node.args) >= 2
            and isinstance(node.args[0], ast.Constant)
            and isinstance(node.args[1], ast.Constant)
            and node.args[1].value == table
        ):
            names.add(node.args[0].value)
    return names


DROPS = [
    # migration file, tables it drops, columns the downgrade may legitimately omit
    ("0003_drop_jobs.py", ["jobs"], {"jobs": {"result_json"}}),
    ("0004_drop_trees.py", ["trees", "transactions"], {"trees": {"job_id"}}),
]


@pytest.mark.parametrize("filename,tables,exempt", DROPS, ids=[d[0] for d in DROPS])
def test_downgrade_rebuilds_every_column(filename, tables, exempt):
    original = _create_table_calls(INITIAL.read_text(encoding="utf-8"), "upgrade")
    restored = _create_table_calls(
        (VERSIONS / filename).read_text(encoding="utf-8"), "downgrade"
    )

    for table in tables:
        assert table in restored, f"{filename} drops {table} and never recreates it"
        expected = _column_names(original[table]) - exempt.get(table, set())
        actual = _column_names(restored[table])
        # 0002 added jobs.result_json after 0001, so the downgrade carries a
        # column the initial schema does not have. Extra is fine; missing is not.
        missing = expected - actual
        assert not missing, f"{filename} downgrade omits {table} columns: {sorted(missing)}"


@pytest.mark.parametrize("filename,tables,exempt", DROPS, ids=[d[0] for d in DROPS])
def test_downgrade_rebuilds_check_constraints(filename, tables, exempt):
    original = _create_table_calls(INITIAL.read_text(encoding="utf-8"), "upgrade")
    restored = _create_table_calls(
        (VERSIONS / filename).read_text(encoding="utf-8"), "downgrade"
    )

    for table in tables:
        missing = _constraint_names(original[table]) - _constraint_names(restored[table])
        assert not missing, (
            f"{filename} downgrade omits {table} constraints: {sorted(missing)}"
        )


@pytest.mark.parametrize("filename,tables,exempt", DROPS, ids=[d[0] for d in DROPS])
def test_index_names_match_the_ones_that_exist(filename, tables, exempt):
    """A drop_index of a name nothing created fails at runtime, and a downgrade
    that invents names leaves the schema subtly different from the original."""
    initial_source = INITIAL.read_text(encoding="utf-8")
    migration_source = (VERSIONS / filename).read_text(encoding="utf-8")

    for table in tables:
        real = _index_names(initial_source, "upgrade", table)
        dropped = set(re.findall(rf'drop_index\("([^"]+)", table_name="{table}"', migration_source))
        recreated = _index_names(migration_source, "downgrade", table)

        assert not (dropped - real), (
            f"{filename} drops indexes on {table} that 0001 never created: "
            f"{sorted(dropped - real)}"
        )
        assert not (recreated - real), (
            f"{filename} downgrade creates indexes on {table} under names 0001 "
            f"never used: {sorted(recreated - real)}"
        )


def test_the_migration_chain_is_unbroken():
    revisions, downs = {}, {}
    for path in sorted(VERSIONS.glob("[0-9]*.py")):
        text = path.read_text(encoding="utf-8")
        revisions[path.name] = re.search(r'^revision: str = "([^"]+)"', text, re.M).group(1)
        down = re.search(r"^down_revision: [^=]+= (.+)$", text, re.M).group(1).strip()
        downs[path.name] = None if down == "None" else down.strip('"')

    ids = set(revisions.values())
    assert len(ids) == len(revisions), "two migrations share a revision id"
    for name, parent in downs.items():
        if parent is not None:
            assert parent in ids, f"{name} has down_revision {parent!r}, which no file defines"
    roots = [name for name, parent in downs.items() if parent is None]
    assert len(roots) == 1, f"expected exactly one root migration, found {roots}"
