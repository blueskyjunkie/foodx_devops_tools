#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import contextlib
import pathlib

import pytest

from foodx_devops_tools.validate_configuration import _main
from tests.ci.support.click_runner import (  # noqa: F401
    click_runner,
    isolated_filesystem,
)

# Due to validation checks in pipeline configuration, each "good" sample must
# be self-consistent with all other samples.
SAMPLES = {
    "clients.yml": {
        "good": """---
clients:
  c1:
    release_states:
      - r1
    system: sys1
""",
        "bad": "",
    },
    "deployments.yml": {
        "good": """---
deployments:
  sys1-c1-r1:
    locations:
      - loc1
      - loc2
    subscription: sub1
""",
        "bad": "",
    },
    "release_states.yml": {
        "good": """---
release_states:
  - r1
""",
        "bad": "",
    },
    "subscriptions.yml": {
        "good": """---
subscriptions:
  sub1:
    ado_service_connection: some-name
    azure_id: abc123
    tenant: t1
""",
        "bad": "",
    },
    "systems.yml": {
        "good": """---
systems:
  - sys1
""",
        "bad": "",
    },
    "tenants.yml": {
        "good": """---
tenants:
  t1:
    azure_id: abc123
    azure_name: some name
""",
        "bad": "",
    },
}


@contextlib.contextmanager
def mock_files(
    current_file: str,
    current_state: str,
    expected_dir: pathlib.Path,
    mock_runner,
):
    with isolated_filesystem(str(expected_dir), mock_runner):
        for file, content in SAMPLES.items():
            if file != current_file:
                with (expected_dir / file).open(mode="w") as f:
                    f.write(content["good"])
            else:
                with (expected_dir / file).open(mode="w") as f:
                    f.write(content[current_state])

        yield expected_dir


def test_good_exits_clean(click_runner):
    expected_dir = pathlib.Path("goodpath")
    expected_state = "good"

    with mock_files("clients.yml", expected_state, expected_dir, click_runner):
        result = click_runner.invoke(_main, [str(expected_dir)])

        if result.exit_code != 0:
            pytest.fail(result.output)


def test_bad_exits_dirty(click_runner):
    expected_dir = pathlib.Path("badpath")
    expected_state = "bad"

    is_bad = list()
    failed_names = list()
    for file, content in SAMPLES.items():
        with mock_files(file, expected_state, expected_dir, click_runner):
            result = click_runner.invoke(_main, [expected_dir])

            if result.exit_code == 0:
                failed_names.append(file)
            is_bad.append(result.exit_code != 0)

    if not all(is_bad):
        pytest.fail(
            "Configuration passed validation when fail expected, "
            "{0}".format(failed_names)
        )
