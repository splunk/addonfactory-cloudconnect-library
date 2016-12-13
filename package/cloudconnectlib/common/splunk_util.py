import sys
from ..splunktacollectorlib.data_collection.ta_checkpoint_manager import TACheckPointMgr

check_pointer = None

std_out = sys.stdout.write


def set_check_pointer(checkpointer):
    global check_pointer
    check_pointer = checkpointer


def get_checkpoint():
    global check_pointer
    if check_pointer and isinstance(check_pointer, TACheckPointMgr):
        return check_pointer.get_ckpt()
    else:
        return None


def update_checkpoint(namespaces, value):
    global check_pointer
    if check_pointer and isinstance(check_pointer, TACheckPointMgr):
       check_pointer.update_ckpt(value, namespaces=namespaces)
    else:
        return


def set_std_out(write_events_fn):
    global std_out
    std_out = write_events_fn
