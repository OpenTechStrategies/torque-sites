#!/usr/bin/env python

"""These are tests that ensure our sanitized csv can be fed to
csv2wiki and result in decent mediawiki pages.  They should check for
correct HTML output.  The csv2wiki input expects that.  Fix-csv should
not emit markdown-formatted stuff.

"""

import imp

# We named fix-csv using a dash and left out the .py extension, so
# this is basically just a regular old import:
fix_csv = imp.load_source('fix_csv', 'fix-csv')

fixed = ""
def get_fixed():
    """Do the fix_csv once and then we can run tests on the results.  Note the pare=100.  There should be a test option for quick vs thorough that adjusts pare."""
    global fixed
    if not fixed:
        fixed = fix_csv.fix_csv("100andchangeExport-all-judges.csv", None, 100).getvalue()
    return fixed
   
def test_table_problem():
    fixed = get_fixed()
    print "Every table tag should be closed throughout the input."
    assert fixed.count("<table") == fixed.count("</table>")

def test_fix_anchors():
    fixed = get_fixed()
    assert not "<a href=" in fixed
