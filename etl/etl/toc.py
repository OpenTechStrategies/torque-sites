# All the different kinds of TOCs that we have on our system
#
# At this time the templates come from the python here, because
# they are actually generated.  There's an opportunity to have a
# template that generates jinja templates, but it's probably easier
# to just have them here.


class Toc:
    def process_competition(self, competition):
        """Processes a COMPETITION after it has been built.  This
        is separate from the initializer because we want to
        declare the TOCs somewhere ahead of all the competition
        processing."""
        pass

    def template_file(self):
        """Returns a jinja template file, usually generated in place
        that will be uploaded along with the json file generated
        by the dictionary returned by grouped_data"""
        return ""

    def grouped_data(self):
        """Returns a dictionary that should be uploaded alongside
        the template to be handled by torque with rendering the Toc"""
        return {}


class GenericToc(Toc):
    """A Toc that prints a grouped set of proposals with each group
    being a heading in the eventual wiki page."""

    def __init__(self, name, column, initial_groupings=[]):
        self.name = name
        self.column = column
        self.groupings = initial_groupings
        self.data = {x: [] for x in initial_groupings}

    def process_competition(self, competition):
        self.competition_name = competition.name
        for proposal in competition.ordered_proposals():
            grouping = proposal.cell(self.column)
            if grouping not in self.data:
                self.groupings.append(grouping)
                self.data[grouping] = []
            self.data[grouping].append(proposal.key())

    def template_file(self):
        template = "__TOC__\n"
        template += "{% for group_name, proposal_ids in groups.items() %}\n"
        template += "    {%- set proposals_in_group = [] %}\n"
        template += "    {%- for proposal_id in proposal_ids %}\n"
        template += (
            "        {%%- if proposal_id in %s.keys() %%}\n" % self.competition_name
        )
        template += '            {{- "" if proposals_in_group.append(proposal_id) }}\n'
        template += "        {%- endif %}\n"
        template += "    {%- endfor %}\n"
        template += "    {%- if proposals_in_group|length > 0 %}\n"

        # This line is so that we can have counts and still link into it
        template += "<div id='{{ group_name }}'></div>\n"
        template += "= {{ group_name }} ({{ proposals_in_group|length }}) =\n"
        template += "        {%- for proposal_id in proposals_in_group %}\n"
        template += "* {{ toc_lines[proposal_id] }}\n"
        template += "        {%- endfor %}\n"
        template += "    {%- endif %}\n"
        template += "{%- endfor %}\n"
        return template

    def grouped_data(self):
        return {"groups": self.data}


class GenericMultiLineToc(GenericToc):
    """A special case of GenericToc for columns that have multiple
    values in them (like a list of keywords), so that proposals
    can show up multiple times on the Toc"""

    def process_competition(self, competition):
        self.competition_name = competition.name
        for proposal in competition.ordered_proposals():
            groupings = proposal.cell(self.column).split("\n")
            for grouping in groupings:
                if grouping not in self.data:
                    self.groupings.append(grouping)
                    self.data[grouping] = []
                self.data[grouping].append(proposal.key())


class ListToc(Toc):
    """A Toc that just lists all the proposals someone has access to."""

    def __init__(self, name):
        self.name = name

    def process_competition(self, competition):
        self.competition_name = competition.name
        self.keys = [p.key() for p in competition.ordered_proposals()]

    def template_file(self):
        template = "{% for proposal_id in proposal_ids %}\n"
        template += (
            "    {%%- if proposal_id in %s.keys() -%%}\n" % self.competition_name
        )
        template += "* {{ toc_lines[proposal_id] }}\n"
        template += "{% endif -%}\n"
        template += "{% endfor %}\n"
        return template

    def grouped_data(self):
        return {"proposal_ids": self.keys}


class GeographicToc(Toc):
    """A toc where the grouping is multi level.  For instance, for a given
    competition, we might want to group first by Country, then by State, then
    by County, but for another we might want to group by Region, SubRegion, Country,
    AND State.  This Toc handles all the collating of the data, and then puts
    out the toc in a general way."""

    def __init__(self, name, column_sets):
        self.name = name
        self.column_sets = column_sets
        self.data = {}

    def process_competition(self, competition):
        self.competition_name = competition.name

        def add_proposal_to_data(proposal, data, column_set):
            val = proposal.cell(column_set[0]).strip()
            if not val:
                return
            if len(column_set) > 1:
                if val not in data:
                    data[val] = {"shown": False, "subcolumn": {}}
                add_proposal_to_data(proposal, data[val]["subcolumn"], column_set[1:])
            else:
                if val not in data:
                    data[val] = {"shown": False, "proposals": []}
                data[val]["proposals"].append(proposal.key())

        for proposal in competition.ordered_proposals():
            for column_set in self.column_sets:
                add_proposal_to_data(proposal, self.data, column_set)

    def grouped_data(self):
        return {"groups": self.data}

    def template_file(self):
        template = "__TOC__\n"

        template += "{%- for subcolumn_name_0, subcolumn_data_0 in groups.items() %}\n"
        for i in range(1, len(self.column_sets[0])):
            template += (
                '{%%- for subcolumn_name_%s, subcolumn_data_%s in subcolumn_data_%s["subcolumn"].items() %%}\n'
                % (i, i, i - 1)
            )

        template += '{%%- for proposal_id in subcolumn_data_%s["proposals"] -%%}\n' % (
            len(self.column_sets[0]) - 1
        )
        template += "{%% if proposal_id in %s.keys() %%}\n" % self.competition_name
        template += '{%- if not subcolumn_data_0["shown"] -%}\n'
        template += '{%- set _ = subcolumn_data_0.update({"shown": True }) %}\n'
        template += "= {{ subcolumn_name_0 }} =\n"
        for i in range(1, len(self.column_sets[0])):
            template += "{%- endif -%}\n"
            template += '{%%- if not subcolumn_data_%s["shown"] -%%}\n' % i
            template += (
                '{%%- set _ = subcolumn_data_%s.update({"shown": True }) %%}\n' % i
            )
            template += "%s {{ subcolumn_name_%s }} %s\n" % (
                "=" * (i + 1),
                i,
                "=" * (i + 1),
            )

        template += "{% endif -%}\n"
        template += "* {{ toc_lines[proposal_id] }}\n"
        template += "{% endif -%}\n"
        template += "{% endfor %}\n"
        for _ in range(len(self.column_sets[0])):
            template += "{%- endfor %}\n"

        return template
