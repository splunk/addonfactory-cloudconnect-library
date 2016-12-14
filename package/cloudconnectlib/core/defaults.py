"""Default config for cloud connect"""

timeout = 120  # request timeout is two minutes

disable_ssl_cert_validation = False  # default enable SSL validation

success_statuses = (200, 201)  # statuses be treated as success.

retries = 3

# response status which need to retry.
retry_statuses = (429, 500, 501, 502, 503, 504, 505, 506, 507,
                  509, 510, 511)

# response status which need print a warning log.
warning_statuses = (203, 204, 205, 206, 207, 208, 226,
                    300, 301, 302, 303, 304, 305, 306, 307, 308)
