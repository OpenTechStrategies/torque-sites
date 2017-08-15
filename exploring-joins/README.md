https://github.com/OpenTechStrategies/MacFound/issues/38#issuecomment-322021507
explains how doing an inner join with 'csvjoin' caused some rows to be
dropped.

* fun-with-joins

  A script demonstrating the kind of join we need to do, using
  easy-to-follow sample data.

* join-test-main-org-data.csv,
  join-test-supplemental-person-data.csv,
  join-test-supplemental-person-data-missing-59-23-41.csv

  Sample data for the 'fun-with-joins' script.  The script actually
  only uses the first and third of these files, but the second is
  there to show what the complete supplemental data would be.  Do

    $ diff -u join-test-supplemental-person-data.csv \
              join-test-supplemental-person-data-missing-59-23-41.csv
  
  to see what data is removed for the "missing rows" case.

* principal-contacts-supplement-all-review-numbers.txt

  This is just the list of all review numbers from the rows in
  "Principal-contact-join-20170716-utf8.csv", which the MacArthur
  Foundation sent to us on 21 July 2017.

* reasons-for-turndown-supplement-all-review-numbers.txt

  Like the above, but "Reason-for-Turndown-join-2017-07-16-utf8.csv".

* contacts-not-in-reasons.txt,
  reasons-not-in-contacts.txt

  These two files show the crosswise missing review numbers.  First,
  all review numbers in "Principal-contact-join-20170716-utf8.csv"
  that were not in "Reason-for-Turndown-join-2017-07-16-utf8.csv";
  second, all those "Reason-for-Turndown-join-2017-07-16-utf8.csv"
  that were not in "Principal-contact-join-20170716-utf8.csv".
