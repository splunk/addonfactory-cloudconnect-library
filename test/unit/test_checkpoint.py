import json
import os
import os.path as op

from cloudconnectlib.core.checkpoint import CheckpointManagerAdapter


def test_checkpoint_manager_adapter():
    task_conf = {
        'appname': 'TEST_APPNAME',
        'stanza_name': 'TEST_STANZA_NAME'
    }
    checkpoint_dir = op.join(op.dirname(op.abspath(__file__)), 'checkpoint_dir')
    os.makedirs(checkpoint_dir, exist_ok=True)

    meta_conf = {
        'checkpoint_dir': checkpoint_dir
    }
    namespaces = '{{name}}'
    content = {'checkpoint': '{{checkpoint}}'}

    cmgr = CheckpointManagerAdapter(namespaces, content, meta_conf, task_conf)

    cmgr.save({'name': 'TEST_NAME', 'checkpoint': 'CHECKPOINT'})

    filename = op.join(checkpoint_dir, cmgr.get_ckpt_key(['TEST_NAME'])[0])
    with open(filename, 'r') as fp:
        assert json.load(fp)['data'] == {
            'checkpoint': 'CHECKPOINT'
        }

    if op.exists(filename):
        os.remove(filename)
    if op.exists(checkpoint_dir):
        os.removedirs(checkpoint_dir)
