"""
Root conftest.py.

If the `cryptography` package is not functional (e.g. broken system install,
missing _cffi_backend, pyo3 panic on import), skip the cryptography-dependent
test files at collection time rather than letting their import crash pytest.

The skip is printed to stderr so it never silently disappears — a green run
with N fewer tests should always be loud about why.
"""

import subprocess
import sys

CRYPTO_TEST_FILES = [
    "tests/test_pcea.py",
    "tests/test_theta.py",
]


def _cryptography_ok() -> bool:
    result = subprocess.run(
        [sys.executable, "-c", "from cryptography.hazmat.primitives import hashes"],
        capture_output=True,
    )
    return result.returncode == 0


if not _cryptography_ok():
    collect_ignore = list(CRYPTO_TEST_FILES)
    sys.stderr.write(
        "conftest: cryptography import failed; ignoring "
        + ", ".join(CRYPTO_TEST_FILES)
        + "\nconftest: install/repair `cryptography>=41` to re-enable these tests.\n"
    )
