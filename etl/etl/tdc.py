# A set of utilities that are made to dump out to the tdcconfig
# directory, that while aren't directly used by etl pipelines to
# upload anything, provide extra contextual information for
# people running the pipelines.
#
# For instance, AllProposals will dump out a file meant to go
# in the TorqueConfig on the wiki, like AllColumns.  These would
# represent permission for all the proposals, and all the columns,
# respectively.  Another utility here is a dump out of the entire
# spreadsheet after the etl pipeline is run.
#
# None of these are used by the pipeline, but all may be useful to
# the uploader for debugging and setup of the wikis.

import os
import csv
from etl import competition


def proposal_to_title_line(proposal):
    """Returns a wiki list item that will be parsed by torque"""
    return "* %s: [[%s]]\n" % (
        proposal.key(),
        proposal.cell(competition.MediaWikiTitleAdder.title_column_name),
    )


class AllProposals:
    """Dumps out all the proposals in the form that can be used by
    torque configuration (linked to by the TorqueConfig:MainConfig)"""

    def __init__(self, competition):
        self.competition = competition

    def generate(self, config_dir):
        with open(os.path.join(config_dir, "AllProposals"), "w") as f:
            f.writelines(
                [
                    proposal_to_title_line(p)
                    for p in self.competition.ordered_proposals()
                ]
            )
        print("AllProposals written to TDC config dir")


class ValidProposals:
    """Dumps out the valid proposals (according to COLUMN, checked against KEYWORD)
    in the form that can be used by torque configuration (linked to by the
    TorqueConfig:MainConfig"""

    def __init__(self, competition, column, keyword):
        self.competition = competition
        self.column = column
        self.keyword = keyword

    def generate(self, config_dir):
        with open(os.path.join(config_dir, "ValidProposals"), "w") as f:
            f.writelines(
                [
                    proposal_to_title_line(p)
                    for p in self.competition.ordered_proposals()
                    if p.cell(self.column) == self.keyword
                ]
            )
        print("ValidProposals written to TDC config dir")


class AllColumns:
    """Dumps out the list of all the columns in a competition in the form
    that can be used by the torque config parser"""

    def __init__(self, competition):
        self.competition = competition

    def generate(self, config_dir):
        with open(os.path.join(config_dir, "AllColumns"), "w") as f:
            f.writelines("* %s\n" % column for column in self.competition.columns)

        print("AllColumns written to TDC config dir")


class ProcessedSpreadsheet:
    """Dumps out the final spreadsheet that gets uploaded to torque on to disk."""

    def __init__(self, competition):
        self.competition = competition

    def generate(self, config_dir):
        with open(os.path.join(config_dir, "etl-processed.csv"), "w") as f:
            self.competition.to_csv(f)

        print("etl-processed.csv written to TDC config dir")
