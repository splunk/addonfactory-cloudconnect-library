# README

Splunk CloudConnect SDK is an open source packaged engine for getting data into Splunk using modular inputs.
This SDK is used by Splunk Add-on builder, and Splunk UCC based add-ons and is intended for use by partner
developers. This SDK/Library extends the Splunk SDK for python

## Python compatibility

Starting with version 4.0.0, CloudConnect requires Python 3.9 through 3.13
(`>=3.9,<3.14`). Python 3.7 and 3.8 are no longer supported. Add-ons that vendor
this library must use a supported Python interpreter for both building and
running the add-on.

Version 4.0.0 also requires Jinja2 3.1.6 or later and Munch 3.x. Add-on Builder's
Jinja2 3.1.6 pin satisfies the new Jinja2 minimum.

## Known dependency limitations

Requests is constrained to `>=2.32.5,<2.33` to retain Python 3.9 compatibility.
This range remains affected by [CVE-2026-25645](https://github.com/psf/requests/security/advisories/GHSA-gc5v-m9x4-r6x2).
Upstream limits the affected usage to direct calls to `extract_zipped_paths()`;
CloudConnect does not call that function.

The Splunk dependencies currently require urllib3 below version 2, so updating
the lockfile alone cannot resolve the outstanding urllib3 security findings.
Compatible upstream dependency releases are needed to remove that constraint.

The release candidate's FOSSA scan also reports a denied Unicode-3.0 license in
idna 3.19 and a flagged MPL-2.0 license in certifi. These open findings require
resolution or documented disposition before publication.

## Deprecation

**cloudconnect library drops support of socks4 and http_no_tunnel proxy protocols**.
From cloudconnect library v3.1.0 and above, the socks4 and http_no_tunnel are no longer supported as the library now uses [requests](https://github.com/psf/requests) library for API calls.

## Support

Splunk CloudConnect SDK is an open source product developed by Splunkers. This SDK is not "Supported Software" by Splunk, Inc. issues and defects can be reported
via the public issue tracker.

## Releasing

CI runs the unit suite with runner Python 3.9 against pinned Splunk Enterprise
9.4.16 and 10.6.1.1 installations, and with Python 3.13 against Splunk 10.6.1.1.
The Splunk archives are checked against pinned
SHA512 checksums. Update each version, build ID, and checksum together using the
[official downloads](https://www.splunk.com/en_us/download/previous-releases.html)
and [current release](https://www.splunk.com/en_us/download/splunk-enterprise.html).
The matrix tests both endpoints of the library's supported Python range.

Pushes to `main` publish stable releases; pushes to `develop` publish beta
releases when semantic-release finds a release-worthy commit. Release notes and
the next version are generated automatically from commit messages.

Before merging, update `pyproject.toml` and `cloudconnectlib/__init__.py` to the
version semantic-release will select, refresh `poetry.lock` with Poetry 1.8.5,
and validate the tests and package build. The workflow does not update the
package version fields. Resolve or obtain documented dispositions for the open
security and license findings before release.

For 4.0.0, preserve this footer in the commit that reaches `main`, including the
squash commit message when using squash merge:

```text
BREAKING CHANGE: Python 3.7 and 3.8 are no longer supported.
Requires Python >=3.9,<3.14.
```

After merging, verify both the GitHub release and PyPI publication. Review the
generated release notes and add the known dependency limitations explicitly.

## Contributing

We do not accept external contributions at this time.

## License

* Configuration and documentation licensed subject to [APACHE-2.0](LICENSE)
