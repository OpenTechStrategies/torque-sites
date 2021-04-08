# Default Template for new competitions

This document outlines the process of creating a new competition.
Please update it if you used it and something wasn't quite correct!

## Questions to ask before creating a new competition

* Is the competition itself confidential?

  Can the existence, name, and logo of the competition be made public?
  If anything needs to be confidential, find that out up front and
  make sure this repository does not expose any of the confidential
  information.

* Is there a competition logo?

* What should shortname be for this competition?  

  This will be the URL slug and the abbreviation used in other places.
  Usually it includes a date, even if it is not yet known whether the
  competition will happen in multiple years.  For example, for the
  "Larson/Lam ICONIQ Impact Award" in 2020, the shortname is
  `LLIIA2020`.

* Okta vs local login?  Both?  Some other SSO service?

* If Okta is used, what should the Okta chiclet's name for this competiton be?

  The Okta chiclet should identify the competition unambiguously and
  should be recognizable to any reasonably informed user.  Here are
  some examples:

    - "100&Change (2020)"
    - "Larsen/Lam ICONIQ Impact Award (2020)"
    - "Lone Star (2020)"

  Usually we just put the date in parentheses after the full name.
  But there can be exceptions: with "Climate2030", for example, we
  didn't put "(2020)" after it because that would be confusing given
  the presence of a date in the competition's actual name.

  (See also the section "Authentication, Authorization, and Okta"
  in [DESIGN.md](/DESIGN.md).)

* What groups/roles will be accessing this competition's data?

  What permissions do the groups need, especially regarding
  attachments?

* Which proposals (rows) should be included?

  I.e., What are the validation criteria?

* Confirm which columns are to be included and which are not.

  After setting up ETL, send the client a list of columns that
  *aren't* included in the template at all, just to confirm.
  
* How should proposals be sorted initially?

* What categorizations do we want to have Tables of Contents for?

* Is any review/evaluation/ranking data included at competition
  creation time?

* Will review spreadsheets be coming later?  

  How many different stages of review will there be?  (This is not
  always knowable in advance, and that's fine, but the more we know
  ahead of time the better.)

* Do we know what followup information (budget tables, etc?) might be coming later?

* Any special instructions regarding attachments?

* What plugin-based features will be enabled?

  - [TeamComments](https://github.com/opentechstrategies/TeamComments)?  

  - [PickSome](https://github.com/opentechstrategies/PickSome)?  (If
    so, we have some config decisions to make: naming, how many
    instances, etc.)

  [SimpleFavorites](https://github.com/opentechstrategies/SimpleFavorites)
  should always be set up by default, as per Jeff's email:
    
        From: Jeff Ubois
        Subject: Re: Climate 2030 set up
        To: Karl Fogel
        CC: Frank Duncan
        Date: Tue, 15 Sep 2020 22:14:13 +0000
        Message-ID: <07CBB723-814E-43AC-B8EA-964412149F7D@macfound.org>

* Is there some existing competition that this new one is similar to? 

  I.e., which template to base this new competition on?
  100Change2020, EO, something else?
  
## New installation todo list

This is a list of things to do when installing a new competition.  Add to this
as more and more gets added.  Some of these instructions reference the OTS
subversion repository, and if you don't have access to that, then you will
probably not get too far on this list.

Below, `<SHORTNAME>` refers to the answer to the shortname question above,
e.g. Climate2030.  This short name should always start with a letter for
legacy reasons (variables get named to this, for now).  `$OTS_DIR` should
be your checkout of the OTS subversion directory, and `$OTS_TOOLS_DIR` should
be the checkout of the tools dir (see the OTS onboarding checklist at
https://svn.opentechstrategies.com/repos/ots/trunk/bureaucracy/onboarding/onboarding-checklist.md ).
In various places, `<COMPETITIONNAME>` also means `<SHORTNAME>`  The reason
for that is because `<SHORTNAME>` really only makes sense relative to this
document, and `<COMPETITIONNAME>` is a more proper name for the placeholder
in the various files in this template directory.

The commands here are assumed to be run from the current directory (the
competitions/template directory)

1. Ensure that LFC has filled out the initial questionnaire (above)
2. Send an email to macfound devops, ccing stakeholders in OTS and LFC, using the template `OktaEmailTemplate`
   - The subject can be something along the lines of:
     - Okta Configuration needed for <COMPETITION LONG NAME>
   - Replace all instances of `<COMPETITIONNAME>` with the SHORTNAME
   - Change anything else in the email to your liking
   - They should respond with a metadata url that will be used in the configuration below
3. Set your SHORTNAME variable
   - `export SHORTNAME=<SHORTNAME>`
4. Create a subversion directory for the new competition, and it's data directory, at:
   - `svn mkdir --parents $OTS_DIR/clients/lever-for-change/torque-sites/$SHORTNAME/data`
5. Create the bigdata directory for this competition
   - `svn mkdir --parents https://svn.opentechstrategies.com/repos/bigdata/trunk/clients/lever-for-change/torque-sites/$SHORTNAME/data`
6. Call get-bigdata in that directory, choosing the checkout option
   - `(cd $OTS_DIR/clients/lever-for-change/torque-sites/$SHORTNAME/data ; $OTS_TOOLS_DIR/get-bigdata)`
7. Get the initial regisitration/attachment zipfile from LFC, and encrypt it into that directory
   - `gpg -o $OTS_DIR/clients/lever-for-change/torque-sites/$SHORTNAME/data/bigdata/<ZIPFILENAME>.gpg --symmetric <LOCATION-OF-ZIPFILE>`
   - Generally, we attempt to retain the original filenames from LFC
   - Use the password gotten from `opass show clients/lever-for-change/data-encryption-key`
8. Copy the template README file, and update it to be accurate
   - `cp SubversionREADME.tmpl $OTS_DIR/clients/lever-for-change/torque-sites/$SHORTNAME/data/bigdata/README`
   - `$EDITOR $OTS_DIR/clients/lever-for-change/torque-sites/$SHORTNAME/data/bigdata/README`
9. Add and commit the initial bigdata information
   - `svn add $OTS_DIR/clients/lever-for-change/torque-sites/$SHORTNAME/data/bigdata/*`
   - `svn ci $OTS_DIR/clients/lever-for-change/torque-sites/$SHORTNAME/data/bigdata/*`
10. Commit the bigdata creation in the subversion directory
    - `svn ci $OTS_DIR/clients/lever-for-change/torque-sites/$SHORTNAME`
11. Create the new torque-sites competition
    - `mkdir ../$SHORTNAME`
12. Copy over the ansible and etl directories from the template
    - `cp -ap ansible ../$SHORTNAME`
    - `cp -ap etl ../$SHORTNAME`
13. Change the files named with `COMPETITIONNAME` as appropriate
    - `mv ../$SHORTNAME/ansible/roles/{COMPETITIONNAME,$SHORTNAME}`
    - `mv ../$SHORTNAME/ansible/{COMPETITIONNAME,$SHORTNAME}.yml`
14. Create an opass file for the accounts with the following:
   ```
* For production accounts (https://torque.leverforchange.org/<SHORTNAME>/):

See clients/macfound/torque-sites/<SHORTNAME>/ansible/prod for
more secret information

** Admin / See ansible file for password
```
    - `opass edit clients/lever-for-change/torque-sites/$SHORTNAME/accounts`
    - This opass file is the placeholder for any accounts that get added
15. Create an opass file for the ansible production secrets
    - Create the secret file `mv ../$SHORTNAME/ansible/inv/prod/group_vars/all/secret{.tmpl,}`
    - `opass edit clients/lever-for-change/torque-sites/$SHORTNAME/ansible/prod`
    - One good source is to use xkcd's password generator
      - https://preshing.com/20110811/xkcd-password-generator/ at time of writing
    - Pay special attention to the password requiring to have no spaces, as this
      is required by the current Book Creator (though this note should be
      changed as soon as we are done with the OTS book creator!)
16. Update all the files in the ansible and etl directories, replacing basically everything
    in angle brackets (`<>`) with the appropriate value.
    - For the `SIMPLESAMLURL_FROMMACFOUND`, you'll need the metadata url from macfound devops
17. Update `<COMPETITIONNAME>.yaml` to remove any roles not to be included in this competition
    - Please update the `COMPETITIONNAME.yaml` file in the template/ansible directory to
      include any new ones that have been added!
18. TODO: update compose-and-upload, using it as a shell
18. TODO: git commit the new competition!
18. TODO: Logo STUFF
19. TODO: MediaWiki TorqueConfig stuff!
20. TODO: 
18. Install locally, and test!


## Post-installation checklist for new competition instances

1. Replace the default Mediawiki logo block ("`$wg_logo`" etc) with the right logo(s):
   - Put the competition-specific logo in place for logged-in users.
   - If the competition is not confidential, the same logo can be displayed to non-logged in users;
     else the Lever for Change logo should be used.
2. Create a `TorqueConfig:MainConfig` page in the competition's wiki.
   (TODO: This item needs more detail.)
3. Does login work?  Often it's via some third-party SSO provider like Okta.
4. Is TOC depth adjusted right?
5. Create TOC link(s) in the left navigation pane.
6. Do you need book-printing to work?  Does it?  You may need to
   fiddle with the template.  (TODO: Say where that template is.)
7. Make sure `ActivityLog` logging is working.
8. Does the `PickSome` feature need to be configured?
9. Does the `TeamComments` feature need to be configured?
10. Does the `SimpleFavorites` feature need to be configured?
11. Are all the [user roles](DESIGN.md#user-groups) working correctly?
    - Log in as each role and make sure you see what you expect to see.
      For example, in a competition that has no finalists yet, someone
      logging in with the "Donor" role might see no proposals!  You
      probably don't want that to be the donor's first experience.

Please add items to this list as needed.
