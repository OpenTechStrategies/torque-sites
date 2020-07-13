# Torque Design

## Overview

Torque allows different groups of people to comment on proposals, and
to indicate favored proposals in some specific way.

The initial system is designed around the needs of grant-making
foundations that are running contests similar to
the [100&Change](https://www.macfound.org/programs/100change/)
competition run by the [MacArthur Foundation](https://macfound.org/)
and [Lever for Change](https://www.leverforchange.org/).  Those latter
two organizations and their partners are supplying the first use
cases, and these requirements are designed with them in mind.
However, we are also trying to keep the system generalizable to other
proposal evaluation processes, and are interested in suggestions or
contributions in that direction.

## Shape of the data.

The fundamental content objects are pages and comments.  Each wiki
page represents one proposal, and every comment is associated with a
particular page (even perhaps with specific text on that page).

Wiki pages are generated automatically generated from
[torque](https://github.com/opentechstrategies/torque) that
operates on a spreadsheet of proposals, one row per proposal, and
thus are not to be edited by users.

Users interact with the data is by making per-page comments, and in
some cases by marking a page via some kind of selector or scoring
interface (e.g., checking a box to indicate "I like this proposal" or
something like that).  Each comment has its own thread.

The system does not use wiki "Talk" pages for commenting, because the
UX isn't quite right.  Instead, we use a system explicitly adapted
for commenting in our style; see our
[extenstion](https://github.com/opentechstrategies/TeamComments).

## Users and their capabilities.

Every user of the system is authenticated; there is no anonymous
access.  Users are:

* Decision Makers - Board Members and the primary users of the system
* Pseudo Decision Makers - Test accounts and support staff that
  want to see the system as Decision Makers do
* Outside Reviewers - People who want to be able to view the proposals,
  but may not have access to all the confidential data
* Foundation staff members - LFC members that support the systems
* Administrators - System administrators who have full rights
* Robots - accounts that do uploading/downloading of data programmatically

Each of these user groups needs to be set up in torque configuration
in order to view data.  In the case of group information coming from
outside (see below about Okta), a mapping needs to be done to these
groups.

## Authentication, Authorization, and Okta

Setting up permissions for those who have logged in via Okta happens
like this:

1. Individual (or group) is enabled in Torque app in Okta
   applications section, with appropriate group set.
2. Logins by that person will show up with Board member preferences.

## Automated deployment and content management

Torque is deployed using [Ansible](https://www.ansible.com/).

But because each Torque site is a wiki, Torque originated pages are
set with a flag that disables editing by non Administrator users.

### Preference for using OS distro packages instead of source installs

Our long-term preference is to depend on the versions of applications
and libraries that are packaged in the underlying operating system
distribution (typically Debian GNU/Linux), rather than, say,
installing from stored source tarballs via ansible.  By using
OS-packaged versions, security updates come in as part of standard OS
updates.

There is still work to be done to reach this goal.  For example, we'll
need to switch to using one instance of MediaWiki across Torque,
albeit with different databases (that is, from an external
perspective, it would continue to look like multiple separate wikis).
[Issue
#56](https://github.com/OpenTechStrategies/torque-sites/issues/56)
describes this in detail, and [issue
#55](https://github.com/OpenTechStrategies/torque-sites/issues/55)
describes a similar situation with SimpleSamlPHP.

## Generating PDF books from sets of articles

Currently, book creation in torque is done through a now-obsolete
system that is what Wikipedia itself formerly used: the
[Collection](ansible/thirdparty/extensions/Collection-REL1_33-8566dd1.tar.gz)
extension.  It depends on (among other things) mwlib, which uses
Python 2.x not 3.x.  Wikipedia itself has temporarily disabled its
Book Creator, which formerly used this extension, and posted a
[timeline](https://www.mediawiki.org/wiki/Reading/Web/PDF_Functionality)
about the disablement and the hoped-for future restoration of book
creation.

This [History
section](https://en.wikipedia.org/wiki/Wikipedia:Books#History) gives
a nice overview of the current state of the onion.  Basically,
single-page PDF generation in mediawiki took a detour through the
now-also-obsolete [Electron](https://www.mediawiki.org/wiki/Electron)
before settling on [Proton](https://www.mediawiki.org/wiki/Proton),
which is now handling single-article PDFs on Wikipedia.org.  However,
as yet there's no code hooking Proton into some kind of article
collection system so that one can generate a book consisting of
multiple articles.  The [Talk page for
Proton](https://www.mediawiki.org/wiki/Talk:Proton) gives more
information, also referring to the German company PediaPress's efforts
to make a new book service called "Collector".  According the History
page that effort is closed source, and according to the Talk page the
effort is running behind schedule, though apparently they have a test
service up at https://pediapress.com/collector.

User [Steelpillow](https://en.wikipedia.org/wiki/User:Steelpillow),
who seems to know a lot about this topic, suggests the [Talk page for
Reading/Web/PDF_Functionality](https://www.mediawiki.org/wiki/Talk:Reading/Web/PDF_Functionality)
as a source of more information.

Meanwhile, there is an independent thing happening at
http://mediawiki2latex.wmflabs.org/.  It converts wiki pages to LaTeX
and PDF, and works with any website running MediaWiki, especially
Wikipedia and Wikibooks.  It's FOSS and written in Haskell, but WMF
doesn't support Haskell, so this is unlikely to become an official
Wikipedia solution although it might be interesting for torque's
purposes.

## Reference

These requirements are
[discussed in more detail](https://chat.opentechstrategies.com/#narrow/stream/45-Lever-for.20Change/topic/hello/near/69877) in
our chat room.
