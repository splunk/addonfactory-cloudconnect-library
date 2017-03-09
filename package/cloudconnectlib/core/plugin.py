from ext import _extension_functions
import os


def cce_pipeline_plugin(func):
    _extension_functions[func.func_name] = func

    def pipeline_func(*args, **kwargs):
        return func(*args, **kwargs)
    return pipeline_func


def init_plugins(plugin_path):
    if os.path.isdir(plugin_path)

