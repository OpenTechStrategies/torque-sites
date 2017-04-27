#!/usr/bin/env python

import imp

# We named fix-csv using a dash and left out the .py extension, so
# this is basically just a regular old import:
fix_csv = imp.load_source('fix_csv', 'fix-csv')

def test_fix_quotes():
    l = fix_csv.fix_csv("100andchangeExport-all-judges.csv", None, 100)
    print r'''There shouldn't be any "" or \"" after we fix the csv.''' 
    assert not "" in l.getvalue()
    
