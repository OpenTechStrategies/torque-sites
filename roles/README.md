### Centralized set of ansible roles

This contains all the roles that are used in multiple competitions.  Each
competition can include these roles in their top level `.yml` file, and then
add on their own customizations after as needed.  Generally, these roles
should be included before customizations, and there may be an order that
they need to be run in in order to run correctly (for example, mediawiki
must be run before a role installing an extension).

See [../INSTALL.md](../INSTALL.md) for more information on how to configure your
system to pick up these roles.

