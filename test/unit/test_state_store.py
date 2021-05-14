import os
import os.path as op
from contextlib import contextmanager

from splunktalib import state_store


@contextmanager
def ignored(*exceptions):
    try:
        yield
    except exceptions:
        pass


def _clean_up(checkpoint_dir, filename):
    with ignored(OSError):
        os.remove(op.join(checkpoint_dir, filename))
    with ignored(OSError):
        os.rmdir(checkpoint_dir)


def test_update_file_state_store():
    checkpoint_dir = op.join(op.dirname(__file__), 'test_checkpoint_dir')
    filename = 'checkpoint_file_for_update'

    _clean_up(checkpoint_dir, filename)

    fss = state_store.FileStateStore(app_name='TestApp', checkpoint_dir=checkpoint_dir)

    checkpoint = fss.get_state(filename)
    assert checkpoint is None
    checkpoint = {
        'a1': 'str',
        'a2': 124,
        'a3': [1, 2, 3]
    }
    fss.update_state(filename, checkpoint)
    checkpoint = fss.get_state(filename)

    assert checkpoint is not None
    assert checkpoint['a1'] == 'str'
    assert checkpoint['a2'] == 124
    assert checkpoint['a3'] == [1, 2, 3]

    _clean_up(checkpoint_dir, filename)


def test_delete_file_state_store():
    checkpoint_dir = op.join(op.dirname(__file__), 'test_checkpoint_dir2')
    filename = 'checkpoint_file_for_delete'

    _clean_up(checkpoint_dir, filename)

    fss = state_store.FileStateStore(app_name='TestApp', checkpoint_dir=checkpoint_dir)
    checkpoint = {
        'a1': 'str',
        'a2': 124,
        'a3': [1, 2, 3]
    }
    fss.update_state(filename, checkpoint)
    checkpoint = fss.get_state(filename)

    assert checkpoint is not None
    assert checkpoint['a1'] == 'str'
    assert checkpoint['a2'] == 124
    assert checkpoint['a3'] == [1, 2, 3]

    fss.delete_state(filename)

    checkpoint = fss.get_state(filename)
    assert checkpoint is None

    _clean_up(checkpoint_dir, filename)
