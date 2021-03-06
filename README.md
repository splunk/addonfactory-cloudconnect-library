# README

Splunk CloudConnect SDK is an open source packaged engine for getting data into Splunk using modular inputs.
This SDK is used by Splunk Add-on builder, and Splunk UCC based add-ons and is intended for use by partner
developers. This SDK/Library extends the Splunk SDK for python


## Deprecation

**cloudconnect library drops support of socks4 and http_no_tunnel proxy protocols**.
From cloudconnect library v3.1.0 and above, the socks4 and http_no_tunnel are no longer supported as the library now uses [requests](https://github.com/psf/requests) library for API calls.

## Support

Splunk CloudConnect SDK is an open source product developed by Splunkers. This SDK is not "Supported Software" by Splunk, Inc. issues and defects can be reported
via the public issue tracker.

## Contributing

We do not accept external contributions at this time.

## License

* Configuration and documentation licensed subject to [APACHE-2.0](LICENSE)
