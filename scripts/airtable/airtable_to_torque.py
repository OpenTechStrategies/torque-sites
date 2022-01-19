from pyairtable import Table
from etl import field_allowlist
from torqueclient import Torque
from utils import competition_mapping
import config

airtable_table_name = "Proposals"

torque = Torque(
    "https://torque.leverforchange.org/GlobalView",
    config.GLOBALVIEW_USER,
    config.GLOBALVIEW_PASSWORD,
)

table = Table(config.AIRTABLE_API_KEY, config.AIRTABLE_BASE_ID, airtable_table_name)

torque_columns = [
    column for group in field_allowlist.allowlist.values() for column in group
]
mismatched_keys = set()
updateable_fields = set()

column_mapping = {
    "Competition": "Competition Name",
}


def torque_comp_name(airtable_name):
    return (
        competition_mapping[airtable_name]
        if airtable_name in competition_mapping
        else None
    )


def convert_to_torque(proposal):
    torque_version = {}
    for field, value in proposal["fields"].items():
        if field in column_mapping:
            torque_version[column_mapping[field]] = value
        elif field not in torque_columns:
            mismatched_keys.add(field)
        else:
            torque_version[field] = value

    if "Competition Name" in torque_version:
        torque_version["Competition Name"] = torque_comp_name(
            torque_version["Competition Name"]
        )
    return torque_version


def compare_to_torque(proposal):
    """PROPOSAL must be a valid torque proposal, as in it has passed
    through CONVERT_TO_TORQUE"""

    if "Competition Name" not in proposal:
        print("Can't compare proposal, as it has no competition name")
        return

    if "Application #" not in proposal:
        print("Can't compare proposal, as it has no application #")
        return

    competition = proposal["Competition Name"]
    app_id = proposal["Application #"]
    torque_proposal = torque.competitions[competition].proposals[app_id]

    if torque_proposal is None:
        print("%s #%s wasn't found in torque" % (competition, app_id))
    else:
        num_to_be_updated = 0
        for field in torque_proposal.keys():
            value = torque_proposal[field]
            if field == "Competition Name":
                value = torque_comp_name(value)
            if value and field in proposal and str(value) != str(proposal[field]):
                updateable_fields.add(field)
                num_to_be_updated += 1
        for field, value in proposal.items():
            if value and field not in torque_proposal.keys():
                updateable_fields.add(field)
                num_to_be_updated += 1
        if num_to_be_updated > 0:
            print(
                "%s #%s would get %s fields updated"
                % (competition, app_id, num_to_be_updated)
            )


for proposal in table.all():
    compare_to_torque(convert_to_torque(proposal))

print("We could udpate the following fields:")
print("\n".join(sorted(list(updateable_fields))))
print()
print("When converting, %d keys were unable to match" % len(mismatched_keys))
print("\n".join(sorted(list(mismatched_keys))))
