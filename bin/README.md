Use `find-multi-competition-orgs` to figure out, via the Torque API,
which organizations have submitted multiple proposals, whether to the
same competition or to multiple competitions.

First, create a config file -- the edits should be obvious:

      $ cp lfc-competitions.cfg.tmpl lfc-competitions.cfg
      $ ${EDITOR} lfc-competitions.cfg

(Note that if you're at OTS and have access to opass, then you can just
run `ots-make-lfc-competitions-config` to create the config file from
the template automagically.)

Next, read the program's help to learn about its output:

      $ ./find-multi-competition-orgs --help

If everything there looks good, then just do this:

      $ ./find-multi-competition-orgs --config lfc-competitions.cfg > orgs-report.csv

Voilà!  `orgs-report.csv` has your data.  

Note that you may see some warnings on stderr.  As long as they're
just warnings and not errors, they are not showstoppers and your CSV
output should still be fine.

A few remarks about the source data:

The LLIIA2020 and LoneStar2020 competitions apparently don't have a
unique identifier for the organization.  That is, unlike other
competitions, they don't have an "EIN" column or some equivalent
column.  We can still match by org name, but it's definitely harder
without the EIN or some other unique ID.

Also, the API only returns proposals that were complete enough to be
submitted for validity review.  That is, the API will fetch both valid
and invalid proposals, but even the invalid ones still have some basic
level of completeness.  Therefore, the CSV generated here only
considers those proposals.
