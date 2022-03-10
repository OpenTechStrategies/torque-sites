# Generates a list of all known airtable instances of proposals.
#
# Useful for populating the config.py's TORQUE_PROPOSALS_TO_SYNC
# via copy/paste from output.  Use when you want to run torque_to_airtable.py
# on ALL proposals.

from pyairtable import Table
from utils import competition_mapping
import config
table = Table(config.AIRTABLE_API_KEY, config.AIRTABLE_BASE_ID, "Proposals")

todo = {}
for airtable_prop in table.all():
    if "Application #" in airtable_prop["fields"]:
        comp = competition_mapping[airtable_prop["fields"]["Competition Name"]]
        if comp not in todo:
            todo[comp] = []
        todo[comp].append(airtable_prop["fields"]["Application #"])

print(todo)
