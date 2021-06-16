# Base Install

Each support system is an ansible playbook for installing one of the
requirements for a running torque-site.  They are kept independent
of the competition ansible playbooks to prevent repetition and
overhead when deploying.

Each one has an ansible directory for deployment, and within that
is playbook to run.  See [INSTALL.md](INSTALL.md) for more information.

The current set includes:

* docswiki - a non competition wiki that houses all the torque documentation.
  This is unique in that it is open to the public, but editing is limited
  to members of LFC
* simplebook - python and node service to support book printing
  for MediaWiki.  See [it's page](https://github.com/opentechstrategies/SimpleBook)
  for more information.
* simplesaml - php service to integrate with saml based single signons.
  We currently use it for Okta for certain competitions.  See
  [the main simplesamlphp site](https://simplesamlphp.org/) for more
  information.
* torquedata - Ansible scripts to install the
  [torque system](https://github.com/opentechstrategies/torque/)
  mentioned above.
