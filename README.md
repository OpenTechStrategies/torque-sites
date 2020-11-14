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

The following is the subdirectories

1. [base/](base/) - The base support systems needed for a torque-sites server
2. [etl/](etl/) - Generalized ETL Pipeline
3. [roles/](roles/) - Centralized set of ansible roles for competitions
4. [thirdparty/](thirdparty/) - Supporting files
5. [competitions/](competitions/) - The deployed competitions
6. [scripts/](scripts/) - Miscellaneous scripts for use in conjunction with the project

Because each adheres to the standards set out in these top level
documents, most of the information needed is here.  However, each
competition includes a README that notes information about the
competition as well as other installation reqruirements if applicable.
