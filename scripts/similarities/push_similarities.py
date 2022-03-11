# Pushes the similarities from similarties.csv to the GlobalView
# "Similar Proposals" field, used in the Similar Proposals tab
# Only pushes the 5 most similar.
#
# Get the similarities.csv via the following command:
#
# gpg --decrypt $OTS_DIR/clients/lever-for-change/torque-sites/GlobalView/data/bigdata/similarities.csv.gpg > similarities.csv
#
# Then set up the config.py (via cp config.py{.tmpl,})
#
# Then run via python3 push_similarities.py

from torqueclient import Torque
import config
import csv

torque = Torque(
    "https://torque.leverforchange.org/GlobalView",
    config.GLOBALVIEW_USER,
    config.GLOBALVIEW_PASSWORD,
)

competition_mapping = {
    "RE2020": "RacialEquity2030",
    "100andchange": "100Change2020",
    "ECWC2020": "ECW2020",
    "2030ClimateChallenge": "Climate2030",
    "LSP2020": "LoneStar2020",
    "SDA2021": "Democracy22",
    "chicagoprize": "ChicagoPrize",
    "eoc2019": "EO2020",
    "LLIIA2020": "LLIIA2020",
}

def proposal_torque_uri(proposal):
    competition = proposal["Competition Name"]
    if competition == "100Change2020":
        competition = "LFC100Change2020"

    return "competitions/%s/proposals/%s.mwiki" % (competition, proposal["Application #"])

def convert_proposal_id(proposal_id):
    [comp, id] = proposal_id.split("-")
    return {
        "Competition Name": competition_mapping[comp],
        "Application #": id
    }
    return proposal_id

def proposal_to_globalview_id(proposal):
    return "%s_%s" % (proposal["Competition Name"], proposal["Application #"])

similarities_reader = csv.reader(open("similarities.csv", encoding="utf-8"), delimiter=",", quotechar='"')

next(similarities_reader)

for [proposal_id, similar_proposal_ids, distances] in similarities_reader:
    proposal = convert_proposal_id(proposal_id)
    similar_proposals = []
    for (similar_proposal_id, distance, idx) in zip(similar_proposal_ids.split(","), distances.split(","), range(5)):
        if idx > 4:
            break
        similar_proposal = convert_proposal_id(similar_proposal_id)
        similar_proposal["Distance"] = float(distance)
        similar_proposal["Torque URI"] = proposal_torque_uri(similar_proposal)
        similar_proposals.append(similar_proposal)

    torque.competitions["GlobalView"].proposals[proposal_to_globalview_id(proposal)]["Similar Proposals"] = similar_proposals
