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

## Which proposals to include.

LFC Torque competitions should include all proposals that made it to
the administrative review stage -- whether they passed that review or
not.  In other words, we don't include proposals where the registrant
never submitted it or where it somehow got disqualified before even
getting to admin review, but other than that we include everything
(and the result of admin review, that is, the proposal's valid/invalid
status, is always one of the fields in a proposal's data).

(Note that as of 2020-11-05, we may not meet the above requirements
for all competitions currently on the production site, and
furthermore, the name of the validity column is not even the same
across the competitions that do have it.  See issues
[#79](https://github.com/OpenTechStrategies/torque-sites/issues/79)
and
[#80](https://github.com/OpenTechStrategies/torque-sites/issues/80)
for more.)

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

### "Local login" (i.e., regular, non-Okta MediaWiki login) is also possible.

After
[much](https://github.com/OpenTechStrategies/torque/wiki/Meeting-Notes#2020-11-20-10am-ct-meeting-about-printinguploads)
[discussion](https://github.com/OpenTechStrategies/torque/wiki/Meeting-Notes#2020-11-19-11am-ct-regular-check-in-meeting),
official policy is give normal wiki-using users Okta accounts, except
maybe in the rarest of circumstances.

However, regular MediaWiki logins can be created if necessary.  These
are known as "local logins" (or "local-login" as the adjectival form:
in case you were searching for it with the hyphen, congratulations,
you found it).

We sometimes use local-login accounts for testing, although now that
OTS folks have Okta accounts that's less common.

*Note that a local-login account must not have "@" in the username.*

In other words, just make it a regular-looking MediaWiki username, not
an email address the way Okta-based accounts are.  The reasons for
this are described in [this
conversation](https://chat.opentechstrategies.com/#narrow/stream/45-Lever-for.20Change/topic/Accounts/near/97563).

Since someone can have both an Okta account and a local-login account,
and since competition wikis typically redirect non-logged-in visitors
straight to an Okta login page, you need ask for local login page
explicitly, like this:

      https://torque.leverforchange.org/COMPETITION/locallogin.php

(Note: The cookie will expire in an hour, and you can turn it off any
time via `.../?locallogin=off`.)

LFC Torque sites don't have a "logout" button, because normal users
never need to log out -- Okta keeps them permanently logged in and
re-prompts them for authentication information periodically.  But
local-login users may need to log out explicitly (for example, to
switch over to their Okta-based account).  Here's how to log out:

      https://torque.leverforchange.org/COMPETITION/index.php/Special:UserLogout

(Note that Frank Duncan [got a patch merged upstream into MediaWiki's
PluggableAuth extension](https://gerrit.wikimedia.org/r/c/mediawiki/extensions/PluggableAuth/+/589849)
so that MediaWiki will show a logout button when a user is locally
logged in (there's an internal `LocalLogin` variable that tracks
this).  So once we have deployed a new enough version of MediaWiki,
the special logout instructions here will no longer be needed.)

### User Groups

We use the same authorization groups across competitions whenever
possible, since access patterns tend to be the same.  The roles we've
settled on are listed below (the "LFC" prefix helps MacFound IT track
them in Okta).  See
[roles/permissions/files/default-permissions.php](roles/permissions/files/default-permissions.php)
for technical details of each role's access permissions.

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
  such as viewing logs, creating new users, etc.  (Note: There is a
  legacy group **`LFC Torque Admin`** maintained by MacFound IT.  It
  is [entirely coincident](https://github.com/OpenTechStrategies/torque-sites/blob/ac17a658d245de8d25e1865e341b5706ba2258d0/roles/permissions/files/default-permissions.php#L95)
  with "LFC Admins".  Some day we should vet all of MacFound IT's
  groups and make sure they match this list, but for now, just know
  that these two groups have the same meaning.)


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
meanings.  For historical background, see
[issue #62](https://github.com/OpenTechStrategies/torque-sites/issues/62) and
the [2020-03-17 meeting notes](https://github.com/OpenTechStrategies/torque/wiki/Meeting-Notes#2020-03-17-frankkarl-discussion-re-eo-and-usergroup-permissions).

### Granting API access

API access is currently grated on a per-competition basis.  API users
do not use SSO (Okta) authentication; they must be created with a
["local-login"
account](https://torque.leverforchange.org/COMPETITION/index.php/Special:CreateAccount)
(see above for more about such accounts).

To do the following steps, you should be logged in yourself as "Admin"
via local-login.  (Even if your regular Okta-based account has
permission to create new users, there could be
[complications](https://chat.opentechstrategies.com/#narrow/stream/45-Lever-for.20Change/topic/API/near/97930)
when you try to do some of the steps.  Trust us: it's better just to
be 'Admin' from the start.)

1) [Create the local-login user](https://torque.leverforchange.org/COMPETITION/index.php/Special:CreateAccount).
   We typically use a username of the form `Jrandom.API`, though some
   legacy usernames may not match that form.

2) Send them their password by a secure channel.  (For OTS, record the
   account creation in the appropriate `opass` file too please.)

3) [Put the new user into the appropriate group](https://torque.leverforchange.org/COMPETITION/index.php/Special:UserRights).
   For LFC staff, that group is usually `administrator` (i.e.,
   sysop).  For non-LFC API users, it's usually a dedicated API
   group that has been configured (as per below) to have access to
   just certain columns and/or proposals.  For example, for the MIT
   Knowledge Futures Group, we used `API_KFG` as the group.

4) If necessary, [add permissions configuration for the group](https://torque.leverforchange.org/COMPETITION/index.php/TorqueConfig:MainConfig).
   This involves creating or updating the appropriate row in the
   Permissions table, and it may also involve creating a new Columns
   or Proposals listing page, if the listing page you need doesn't
   already exist.  (For example, the first time you grant a non-LFC
   person API access to a competition, that competition might not
   already have a Columns page that excludes comment fields.)

We had a [long chat on 2020-12-15](https://chat.opentechstrategies.com/#narrow/stream/45-Lever-for.20Change/topic/API/near/97830)
about API account creation.  If you run into a problem with any of the
steps above, or if a step seems to be missing, take a look at that
chat transcript and see if it offers any help.

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
[Issue #56](https://github.com/OpenTechStrategies/torque-sites/issues/56)
describes this in detail, and
[issue #55](https://github.com/OpenTechStrategies/torque-sites/issues/55)
describes a similar situation with SimpleSamlPHP.

## Generating PDF books from sets of articles

Currently, book creation in torque is done through SimpleBook,
a fork of the now obsolete system that is what Wikipedia itself
formerly used: the
[Collection](https://www.mediawiki.org/wiki/Extension:Collection)
extension.

## Reference

These requirements are
[discussed in more detail](https://chat.opentechstrategies.com/#narrow/stream/45-Lever-for.20Change/topic/hello/near/69877) in
our chat room.
