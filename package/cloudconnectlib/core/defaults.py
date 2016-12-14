"""Default config for cloud connect"""

timeout = 120  # request timeout is two minutes

disable_ssl_cert_validation = False  # default enable SSL validation

success_status = (200, 201)  # statuses be treated as success.

retries = 3  # Default maximum retry times.

max_iteration_count = 100  # maximum iteration loop count
