from pyairtable import Table
from pyairtable.formulas import match
from etl import field_allowlist
from torqueclient import Torque
from utils import competition_mapping
import config

airtable_table_name = "Proposals"

def airtable_comp_name(torque_name):
    inverse_mapping = {}
    for key, value in competition_mapping.items():
        inverse_mapping[value] = key
    return (
        inverse_mapping[torque_name]
        if torque_name in inverse_mapping
        else None
    )


def map_annual_operating(operating_budget):
    return {
        "Less than $1 Million": "Less than $1 Million",
        "$1 to $5 Million": "$1.0 to 5 Million",
        "$5 to $10 Million": "$5.1 to 10 Million",
        "$10 to $25 Million": "$10.1 to 25 Million",
        "$25 to $50 Million": "$25.1 to 50 Million",
        "$50 to $100 Million": "$50.1 to 100 Million",
        "$100 to $500 Million": "$100.1 to 500 Million",
        "$1 Billion +": "$1 Billion +",
    }[operating_budget]


def map_legal_status(legal_status):
    return {
        "A private foundation under section 501(c)(3) of the IRC": "A private foundation under section 501(c)(3)",
        "An entity under section 501(c)(3) and 509(a)(1) or (2) of the IRC": "An entity under section 501(c)(3) and 509(a)(1) or (2)",
        "An entity under section 501(c)(4) of the IRC": None,
    }[legal_status]


def map_country(country):
    return {
        "United States": "United States of America",
    }.get(country, country)


def remove_brs(text):
    return text.replace("<br/>", "")


torque = Torque(
    "https://torque.leverforchange.org/GlobalView",
    config.GLOBALVIEW_USER,
    config.GLOBALVIEW_PASSWORD,
)
table = Table(config.AIRTABLE_API_KEY, config.AIRTABLE_BASE_ID, airtable_table_name)
subject_area_table = Table(
    config.AIRTABLE_API_KEY, config.AIRTABLE_BASE_ID, "Subject Areas"
)
priority_populations_table = Table(
    config.AIRTABLE_API_KEY, config.AIRTABLE_BASE_ID, "Priority Populations"
)
organization_table = Table(
    config.AIRTABLE_API_KEY, config.AIRTABLE_BASE_ID, "BSN/Applicant Organizations"
)
domestic_table = Table(config.AIRTABLE_API_KEY, config.AIRTABLE_BASE_ID, "US States")
global_table = Table(config.AIRTABLE_API_KEY, config.AIRTABLE_BASE_ID, "Countries")


def create_or_find_organization(torque_proposal):
    org = organization_table.all(
        formula=match({"Organization Name": torque_proposal["Organization Name"]})
    )
    if len(org) == 0:
        print("Creating an organization for " + torque_proposal["Organization Name"])
        dict_for_creation = {
            "Organization Name": torque_proposal["Organization Name"],
            # "Organization HQ":
            "Organization Legal Status": map_legal_status(
                torque_proposal["Organization Legal Status"]
            ),
            "Annual Operating Budget": map_annual_operating(
                torque_proposal["Annual Operating Budget"]
            ),
            "Organization Website": torque_proposal["Organization Website"],
        }
        return organization_table.create(dict_for_creation)["id"]
    else:
        return org[0]["id"]


def lookup_global_location(location):
    airtable_loc = global_table.all(
        formula=match({"Country Name": map_country(location["Country"])})
    )
    if len(airtable_loc) == 0:
        raise Exception("Couldn't find country %s" % location["Country"])

    return airtable_loc[0]["id"]


def lookup_domestic_location(location):
    airtable_loc = domestic_table.all(
        formula=match({"State Name": location["State/Province"]})
    )
    if len(airtable_loc) == 0:
        raise Exception("Couldn't find state %s" % location["State/Province"])

    return airtable_loc[0]["id"]


def create_airtable_dict(torque_proposal, airtable_proposal_fields={}):
    # Later:
    # UN Sustainable Development Goals (SDGs)
    # Key Partner Organizations (probably not)
    # Funder #1
    # Funder #1: Last Year of Funding
    # Funder #1: Amount of Funding
    # Funder #2
    # Funder #2: Last Year of Funding
    # Funder #2: Amount of Funding
    # Funder #3
    # Funder #3: Last Year of Funding
    # Funder #3: Amount of Funding
    # Sub Regions Covered
    # Regions Covered

    dict = {}

    def in_airtable(key):
        return key in airtable_proposal_fields and airtable_proposal_fields[key]

    if not in_airtable("Primary Subject Area"):
        subject_area = subject_area_table.all(
            formula=match({"Candid Label": torque_proposal["Primary Subject Area"]})
        )
        if len(subject_area) == 0:
            print(
                "Couldn't find subject area: " + torque_proposal["Primary Subject Area"]
            )
        dict["Primary Subject Area"] = [subject_area[0]["id"]]

    if not in_airtable("Priority Populations"):
        priority_populations = []
        for pop in torque_proposal["Priority Populations"]:
            airtable_pop = priority_populations_table.all(
                formula=match({"Candid Label": pop})
            )
            priority_populations.append(airtable_pop[0]["id"])
        dict["Priority Populations"] = priority_populations

    if not in_airtable("Global Current Work Locations"):
        current_global_work_locations = []
        current_domestic_work_locations = []
        for location_num in range(1, 6):
            torque_location = torque_proposal[
                "Current Work #%s Location" % location_num
            ]
            if torque_location:
                if torque_location["Country"] == "United States":
                    current_domestic_work_locations.append(
                        lookup_domestic_location(torque_location)
                    )
                current_global_work_locations.append(
                    lookup_global_location(torque_location)
                )
        dict["Global Current Work Locations"] = (
            list(set(current_global_work_locations))
        )
        dict["U.S. Domestic Current Work Locations"] = (
            list(set(current_domestic_work_locations))
        )

    if not in_airtable("Global Proposed Work Locations"):
        future_global_work_locations = []
        future_domestic_work_locations = []
        for location_num in range(1, 6):
            torque_location = torque_proposal["Future Work #%s Location" % location_num]
            if torque_location:
                if torque_location["Country"] == "United States":
                    future_domestic_work_locations.append(
                        lookup_domestic_location(torque_location)
                    )
                future_global_work_locations.append(
                    lookup_global_location(torque_location)
                )

        dict["Global Proposed Work Locations"] = list(set(future_global_work_locations))
        dict["U.S. Domestic Proposed Work Locations"] = list(set(future_domestic_work_locations))

    if not in_airtable("Lead Organization"):
        organization = create_or_find_organization(torque_proposal)
        dict["Lead Organization"] = [organization]

    # Items that don't cause other requests to airtable
    potential_dict = {
        "Competition Name": airtable_comp_name(torque_proposal["Competition Name"]),
        "Application #": int(id),
        "Project Title": torque_proposal["Project Title"],
        "Project Description": torque_proposal["Project Description"],
        "Project Video": torque_proposal["Video"],
        "Executive Summary": remove_brs(torque_proposal["Executive Summary"]),
        "Annual Operating Budget": map_annual_operating(
            torque_proposal["Annual Operating Budget"]
        ),
        "Number of Full-Time Employees": torque_proposal["Number of Employees"],
        "Lead Organization EIN": torque_proposal["Applicant Tax Identification Number"],
        "Key Partner 1": torque_proposal["Key Partner #1"],
        "Key Partner 2": torque_proposal["Key Partner #2"],
        "Key Partner 3": torque_proposal["Key Partner #3"],
        "Key Partner 4": torque_proposal["Key Partner #4"],
        "Key Partner 5": torque_proposal["Key Partner #5"],
        "Primary Contact": torque_proposal["Primary Contact"]["First Name"]
        + " "
        + torque_proposal["Primary Contact"]["Last Name"],
        "Primary Contact Email": torque_proposal["Primary Contact"]["Email"],
        "Secondary Contact": torque_proposal["Secondary Contact"]["First Name"]
        + " "
        + torque_proposal["Secondary Contact"]["Last Name"],
        "Secondary Contact Email": torque_proposal["Secondary Contact"]["Email"],
        "Lead Organization EIN": torque_proposal["Applicant Tax Identification Number"],
    }

    for key in potential_dict.keys():
        if not in_airtable(key):
            dict[key] = potential_dict[key]

    #print(dict)

    return dict


for competition, ids in config.TORQUE_PROPOSALS_TO_SYNC.items():
    for id in ids:
        proposals = table.all(
            formula=match(
                {
                    "Competition Name": airtable_comp_name(competition),
                    "Application #": int(id),
                }
            )
        )
        torque_proposal = torque.competitions[competition].proposals[id]
        if len(proposals) == 1:
            dict_for_update = create_airtable_dict(
                torque_proposal, proposals[0]["fields"]
            )
            print("Updating %s fields for id %s" % (str(len(dict_for_update)), id))
            table.update(proposals[0]["id"], dict_for_update)
        elif len(proposals) == 0:
            print("Creating id: " + id)
            dict_for_creation = create_airtable_dict(torque_proposal)
            table.create(dict_for_creation)
        else:
            print("FAILURE, TOO MANY APPS IN ARTABLE")
