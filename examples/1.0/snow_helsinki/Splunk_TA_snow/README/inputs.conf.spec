[snow_inputs://<name>]
account = 
interval = 
snow_host = 
sysparm_limit = 
since_when = 
table_name =
builtin_system_checkpoint_storage_type = [auto|file]
# This setting used to set checkpoint storage type.
# If set to 'auto', the input use KV store on search head, use file for other
# instance role.
# If set to 'file', the input always store checkpoint to file.
# Defaults to 'auto'.

builtin_system_use_cache_file = <bool>
# Whether cache checkpoint when checkpoint storage type is file.
# Defaults to true.

builtin_system_max_cache_seconds = <float>
# Maximum cache time in seconds when use cache file to store checkpoint.
# If set to negative float, use default value.
# If set to grater than 3600, use 3600.
# Defaults to 5.

builtin_system_kvstore_collection_name = <string>
# Collection name used to create KV store collection.
# Defaults to input name.