# Torque Sites

Repository of open source code for
[Torque](https://github.com/opentechstrategies/torque/) sites managed
by [Open Tech Strategies, LLC](https://OpenTechStrategies.com/).

The code here is unlikely to be of general use, because it is highly
specific to the needs and datasets of OTS clients (e.g., the
[MacArthur Foundation](https://www.MacFound.org) and [Lever for
Change](https://www.leverforchange.org/)).  We release the code as
open source software anyway, because that's our usual practice and
because some of it could serve as an example or as a template for
other similar efforts, primarily for anyone deploying a Torque-based
service.

See [INSTALL.md](INSTALL.md) and [DESIGN.md](DESIGN.md) for more information.

## Layout of project

Each subdirectory falls into one of three categories:

1. A support system for torque-sites
2. Generalized ETL Pipeline
3. Centralized set of ansible roles for competitions
4. Supporting files
5. A site (competition)

Because each adheres to the standards set out in these top level
documents, most of the information needed is here.  However, each
competition includes a README that notes information about the
competition as well as other installation reqruirements if applicable.

### Support Systems

Each support system is an ansible playbook for installing one of the
requirements for a running torque-site.  They are kept independent
of the competition ansible playbooks to prevent repetition and
overhead when deploying.

Each one has an ansible directory for deployment, and within that
is playbook to run.  See [INSTALL.md](INSTALL.md) for more information.

The current set includes:

* mwlib - python service to support book printing for MediaWiki.
  See [it's page](https://mwlib.readthedocs.io/en/latest/) for more
  information.  Note that this doesn't install the Collection extension
  for MediaWiki, as that's left up to the competition.
* simplesaml - php service to integrate with saml based single signons.
  We currently use it for Okta for certain competitions.  See
  [the main simplesamlphp site](https://simplesamlphp.org/) for more
  information.
* torquedata - Ansible scripts to install the
  [torque system](https://github.com/opentechstrategies/torque/)
  mentioned above.

### Generalized ETL Pipeline

The etl pipelines in the competitions use this code to actually do the
csv composition and uploading.  See [INSTALL.md](INSTALL.md) for more
information on how to get it installed on your system.

The individual competitions etl pipelines are mainly configurations on
this package.

### Centralized set of ansible roles

This contains all the roles that are used in multiple competitions.  Each
competition can include these roles in their top level `.yml` file, and then
add on their own customizations after as needed.  Generally, these roles
should be included before customizations, and there may be an order that
they need to be run in in order to run correctly (for example, mediawiki
must be run before a role installing an extension).

See [INSTALL.md](INSTALL.md) for more information on how to configure your
system to pick up these roles.

### Supporting files

These directories have some general files, usually downloaded from
the internet, that support the ansible scripts.  The reason we download
and commmitted them to this repository rather than downloading them
at time of deploy is to have a reliable cache.  Ideally, this cache
would be on a webserver somewhere under our control, and then this
repository would be more compact, but this is a good stop gap for now.

These are files that are independent of competitions, usually used
by multiple.  For files that a single competition depends on, it may
live in one of these directories or in the competitions ansible tree.

The current set includes:

* thirdparty - tar files of software we depend on

### Competitions

The rest of the directories are competitions that we have deployed.

Each has an ansible and an etl directory.  The former contains the
playbook and support to install that competition, while the latter
can be run after the competition is deployed to install the data.

As noted in [INSTALL.md](INSTALL.md) and above, a lot of the files
necessary to understand and complete the data deployment are confidential,
and so reside on a private server.  The ansible scripts, however,
should be usable by anyone.
