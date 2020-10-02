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
access.  See the "User Groups" section farther down for the kinds of
access permissions users can have.

Each of these user groups needs to be set up in torque configuration
in order to view data.  In the case of group information coming from
outside (see below about Okta), a mapping needs to be done to these
groups.

### Shared user accounts

Some partner organizations may use a shared account -- a single login
used by multiple individuals at that organization.  This kind of
account is no different from any other in terms of how it functions
technically.  This note is merely here to record that, as a matter of
policy, we've decided it's okay to have shared accounts for certain
trusted organizations.

## Authentication, Authorization, and Okta

Setting up permissions for those who have logged in via Okta happens
like this:

1. Individual (or group) is enabled in Torque app in Okta
   applications section, with appropriate group set.
2. Logins by that person will show up with Board member preferences.

### User Groups

We use the same authorization groups across competitions whenever
possible, since access patterns tend to be the same.  The roles we've
settled on are as follows (the "LFC" prefix helps MacFound IT track
them in Okta):

- **`LFC Evaluators`**

  Someone who works with LFC to evaluate the proposals (or some subset
  of proposals) in a competition.  A typical configuration would be
  that they don't have edit ability but can make comments; they don't
  necessarily see all fields or all attachments; and they might get
  anonymized or pseudonymized versions of certain things (e.g.,
  comments, attachments).

  Most LFC Evaluators aren't employees of LFC; they're from
  third-party organizations helping with evaluation.  However, there
  is no reason in principle why one couldn't be an employee of LFC.

- **`LFC Research Partners`**

  Basically the same as "LFC Evaluators", but their purpose is to use
  the proposals as input to some larger analytic goal.  This can
  sometimes result in them having slightly different permissions,
  which is why they are a distinct group.

- **`LFC Staff`**

  People who work at LFC and can see & edit basically everything about
  a proposal.

- **`LFC Admins`**

  Like "LFC Staff", but in addition can perform administrative tasks
  such as viewing logs, creating new users, etc.

- **`LFC Decision Makers`**

  People who make decisions about the fate of proposals.  Typically,
  this is a Board Member or other senior decision-maker at the donor
  organization.  

  The Torque interface is optimized to show decision support features
  to LFC DecisionMakers: e.g., finalist selection, voting, being able
  to see all scores and reviewer comments, etc.

  Furthermore, the interface takes care to avoid showing them things
  that might distract from decision support, such as administrative
  links, edit links, etc.

- **`LFC Pseudo Decision Makers`**

  This is just a group for staff to use when they need to test how
  things look for "LCF Decision Makers".

- **`LFC Robots`**

  Automated bots and processes get this group when they log in.

This section will always hold the canonical list of groups and their
meanings.  For historical background, see [issue
#62](https://github.com/OpenTechStrategies/torque-sites/issues/62) and
the [2020-03-17 meeting
notes](https://github.com/OpenTechStrategies/torque/wiki/Meeting-Notes#2020-03-17-frankkarl-discussion-re-eo-and-usergroup-permissions).

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
