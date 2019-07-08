import tempfile
import textwrap

import pytest


@pytest.fixture
def temp_config():
    with tempfile.NamedTemporaryFile() as config:
        config.write(textwrap.dedent('''
            some-secret: foo secret
        ''').encode('utf-8'))
        config.flush()
        yield config.name
