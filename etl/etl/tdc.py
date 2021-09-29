# A set of utilities that are made to dump out to the tdcconfig
# directory, that while aren't directly used by etl pipelines to
# upload anything, provide extra contextual information for
# people running the pipelines.
#
# For instance, AllProposals will dump out a file meant to go
# in the TorqueConfig on the wiki, like AllColumns.  These would
# represent permission for all the proposals, and all the columns,
# respectively.  Another utility here is a dump out of the entire
# json file after the etl pipeline is run.
#
# None of these are used by the pipeline, but all may be useful to
# the uploader for debugging and setup of the wikis.

import os
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


class Columns:
    """Dumps out the list of all the columns in a competition in the form
    that can be used by the torque config parser"""

    def __init__(self, competition):
        self.competition = competition

    def generate(self, config_dir):
        from etl import field_whitelist

        exceptions = { }
        for (field, group) in self.competition.whitelist_exceptions:
            if group not in exceptions:
                exceptions[group] = []
            exceptions[group].append(field)

        for group in list(set(list(field_whitelist.whitelist.keys()) + list(exceptions.keys()))):
            available_columns = []
            if group in field_whitelist.whitelist:
                available_columns.extend(field_whitelist.whitelist[group])
            if group in exceptions:
                available_columns.extend(exceptions[group])

            with open(os.path.join(config_dir, "%sColumns" % group), "w") as f:
                f.writelines(["* %s\n" % column for column in self.competition.columns if column in available_columns])

            print("%sColumns written to TDC config dir" % group)

        with open(os.path.join(config_dir, "AllColumns"), "w") as f:
            f.writelines(["* %s\n" % column for column in self.competition.columns])
        print("AllColumns written to TDC config dir")


class ProcessedCollection:
    """Dumps out the final object that gets uploaded to torque on to disk in json."""

    def __init__(self, competition):
        self.competition = competition

    def generate(self, config_dir):
        with open(os.path.join(config_dir, "etl-processed.json"), "w") as f:
            self.competition.to_json(f)

        print("etl-processed.json written to TDC config dir")
