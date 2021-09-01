from etl import utils
from etl import Geocoder
import csv
import json
import os
import re
from functools import total_ordering
from enum import Enum


class Competition:
    """A Competition, encapsulating a set of Proposal objects"""

    def __init__(
        self,
        proposals_location,
        name,
        key_column_name,
        pare=None,
        type_row_included=False,
    ):
        """Initializes the competition from the source spreadsheet in
        PROPOSALS_LOCATION (a file location).  Loads up the CSV and processes
        it.

        NAME refers to the name of the competition, KEY_COLUMN_NAME
        is which column in the base csv holds the identifier for the proposal.

        Boolean TYPE_ROW_INCLUDED indicates whether the second row is a list of torque
        column types.  This is useful when the incoming spreadsheet was previously
        generated for torque.

        PARE, when passed in, restricts the number of items as defined by utils.parse_pare"""
        try:
            proposals_reader = csv.reader(
                open(proposals_location, encoding="utf-8"), delimiter=",", quotechar='"'
            )
        except UnicodeDecodeError:
            sys.stderr.write(
                "fix-csv expects utf-8-encoded unicode, not whatever is in this csv file.\n"
            )
            sys.exit(-1)

        self.name = name
        # We strip out \ufeff here because sometimes the spreadsheets we get
        # are edited by macs, and that adds this extra character, which messes
        # up our columns!
        self.columns = [
            col.strip().replace("\ufeff", "") for col in next(proposals_reader)
        ]
        self.key_column_name = key_column_name
        self.column_types = {}
        self.proposals = {}
        self.sorted_proposal_keys = []
        self.tocs = []

        if type_row_included:
            type_row = next(proposals_reader)
            for column_name, column_type in zip(self.columns, type_row):
                self.column_types[column_name] = column_type

        row_num = 0
        key_column_idx = self.columns.index(key_column_name)
        pare_factor, keys_to_include = utils.parse_pare(pare)
        for row in proposals_reader:
            row_num = row_num + 1
            if pare_factor is not None and (row_num % pare_factor) != 0:
                continue

            if (
                keys_to_include is not None
                and row[key_column_idx] not in keys_to_include
            ):
                continue

            proposal = Proposal(self.columns, row, key_column_name)
            key = proposal.key()
            self.sorted_proposal_keys.append(key)
            self.proposals[key] = proposal

    def process_all_cells_special(self, processor):
        """For all cells in the competition, apply CellProcessor PROCESSOR
        to them"""
        for column_name in self.columns:
            self.process_cells_special(column_name, processor)

    def process_cells_special(self, column_name, processor):
        """For cells in the competition at COLUMN_NAME,
        apply the PROCESSOR to them.  PROCESSOR is an object
        of the CellProcessor type."""
        if processor.column_type() is not None:
            self.column_types[column_name] = processor.column_type()

        for proposal in self.proposals.values():
            proposal.process_cell_special(column_name, processor)

    def add_supplemental_information(self, adder):
        """Adds additional columns to the competition via ADDER.  ADDER
        must be of the InformationAdder type.  This will add the
        headers, the column types, and the data."""
        for column_name in adder.column_names():
            if adder.column_type(column_name) is not None:
                self.column_types[column_name] = adder.column_type(column_name)

            # Even though this is meant for adding columns, there are times
            # when adding overwrites columns, such as when merging two sheets
            # together.
            if column_name not in self.columns:
                self.columns.append(column_name)

            for proposal in self.proposals.values():
                proposal.add_cell(column_name, adder.cell(proposal, column_name))

    def sort(self, column_name, is_integer=False):
        """Sorts the competition by the data in COLUMN_NAME.  IS_INTEGER
        declares whether that cell should be converted to an int for
        sorting."""
        if is_integer:
            sorted_proposals = sorted(
                self.proposals.values(),
                key=lambda proposal: int(proposal.cell(column_name)),
            )
        else:
            sorted_proposals = sorted(
                self.proposals.values(), key=lambda proposal: proposal.cell(column_name)
            )
        self.sorted_proposal_keys = [
            proposal.cell(self.key_column_name) for proposal in sorted_proposals
        ]

    def filter_proposals(self, proposal_filter):
        """Removes proposals according to PROPOSAL_FILTER, which needs
        to be an object of the instance ProposalFilter."""
        self.sorted_proposal_keys = [
            k
            for k in self.sorted_proposal_keys
            if not proposal_filter.filter_proposal(self.proposals[k])
        ]
        self.proposals = {k: self.proposals[k] for k in self.sorted_proposal_keys}

    def ordered_proposals(self):
        """Returns an array of Proposals ordered by the current sort"""
        return [self.proposals[k] for k in self.sorted_proposal_keys]

    def to_csv(self, output):
        """Writes a csv out to stream OUTPUT designed to be uploaded to a
        torque instance"""
        csv_writer = csv.writer(
            output, delimiter=",", quotechar='"', lineterminator="\n"
        )
        csv_writer.writerow(self.columns)

        # The column types, as an array in the order of the header columns
        csv_writer.writerow(
            [
                (self.column_types[col] if col in self.column_types else "")
                for col in self.columns
            ]
        )
        for proposal in self.ordered_proposals():
            csv_writer.writerow(proposal.to_csv(self.columns))

        return output

    def add_toc(self, toc):
        """Adds a toc.Toc to this competition."""
        self.tocs.append(toc)

    def process_tocs(self):
        """Processes all the tocs.  Usually should be done after the
        competition is completely assembled."""
        for toc in self.tocs:
            toc.process_competition(self)


class Proposal:
    """A Proposal, of which there are many in a competition.  A Proposal
    loosely represents one row in the master spreadsheet, but provides
    indexing based on names, ability to add new fields, etc"""

    def __init__(self, column_names, row, key_column_name):
        """COLUMN_NAMES are the list of columns that came from the
        initial spreadsheet, while ROW is the value for this proposal.
        KEY_COLUMN_NAME is used to later get the key of this proposal.

        This sets up the proposal by processing the initial row"""
        self.data = dict(zip(column_names, row))
        self.key_column_name = key_column_name

    def add_cell(self, column_name, cell):
        """Adds a new value CELL to the place held by COLUMN_NAME"""
        self.data[column_name] = cell

    def process_cell_special(self, column_name, processor):
        """Process a cell noted by COLUMN_NAME from PROCESSOR of type CellProcessor"""
        self.data[column_name] = processor.process_cell(self, column_name)

    def cell(self, column_name):
        """Returns the cell value for COLUMN_NAME"""
        if column_name in self.data:
            return self.data[column_name]

    def key(self):
        """Returns the key for this Proposal"""
        return self.cell(self.key_column_name)

    def to_csv(self, column_names):
        """Transforms this Proposal into an array for output, ordered by
        COLUMN_NAMES"""
        return [self.cell(column_name) for column_name in column_names]


class ProposalFilter:
    """The base class for Proposal Filters, which will usually implement
    filter_proposal"""

    def filter_proposal(self, proposal):
        """Return whether the proposal matches this filter, and should be
        filtered.  Should be over loaded"""
        return True


class ColumnEqualsProposalFilter(ProposalFilter):
    """A basic filter for when the value in a given column matches
    the setup value"""

    def __init__(self, column_name, value):
        self.column_name = column_name
        self.value = value

    def filter_proposal(self, proposal):
        return proposal.cell(self.column_name) == self.value


class ColumnNotEqualsProposalFilter(ProposalFilter):
    """A basic filter for when the value in a given column fails to match
    the setup value"""

    def __init__(self, column_name, value):
        self.column_name = column_name
        self.value = value

    def filter_proposal(self, proposal):
        return proposal.cell(self.column_name) != self.value


class CellProcessor:
    """The base class for Cell Processors, which implement column_type
    and process_cell"""

    def column_type(self):
        """Return the torque type of the column, or None if using the default
        column type"""
        return None

    def process_cell(self, proposal, column_name):
        """Transforms the PROPOSAL, in COLUMN_NAME, to some other value, and
        returns it."""
        return proposal.cell(column_name)


class FixCellProcessor(CellProcessor):
    """A CellProcessor that calls utils.fix_cell on the cells affected.
    That function cleans up irregular data"""

    def __init__(self):
        self.processed_cells = {}

    def process_cell(self, proposal, column_name):
        key = proposal.key()
        if key not in self.processed_cells:
            self.processed_cells[key] = {"cols": 0, "fixed": 0}

        cell = proposal.cell(column_name)
        fixed_cell = utils.fix_cell(cell)
        self.processed_cells[key]["cols"] += 1
        if fixed_cell != cell:
            self.processed_cells[key]["fixed"] += 1
        return fixed_cell

    def report(self):
        for key, report in self.processed_cells.items():
            print(
                "Sanitized row %s (%d cols, %d fixed)."
                % (key, report["cols"], report["fixed"])
            )


class RemoveHTMLBRsProcessor(CellProcessor):
    """A CellProcessor that removes any HTML BR's that were added
    as part of the cleanup process, usually by the FixCellProcessor"""

    def __init__(self, replacement_string=""):
        self.replacement_string = replacement_string

    def process_cell(self, proposal, column_name):
        # Because of how fix_cell works, we have to remove both the <br> and the \n separately
        return (
            proposal.cell(column_name)
            .replace("<br/>", "")
            .replace("\n", self.replacement_string)
        )


class MultiLineProcessor(CellProcessor):
    """A CellProcessor that splits a cell on the initialized SPLIT_STRING
    (defautling to comma: ",") into a newline separate list, for torque
    to represent as a list"""

    def __init__(self, split_string=","):
        self.split_string = split_string

    def column_type(self):
        return "list"

    def process_cell(self, proposal, column_name):
        cell = proposal.cell(column_name)
        return "\n".join([elem.strip() for elem in cell.split(self.split_string)])


class MultiLineFromListProcessor(CellProcessor):
    """A CellProcesor that splits a cell into multiple lines, but does
    so based on a passed in list, verifying that each item appears
    in the list, and allowing list items to have commas in them."""

    def __init__(self, valid_list):
        self.valid_list = valid_list

    def column_type(self):
        return "list"

    def process_cell(self, proposal, column_name):
        cell = proposal.cell(column_name).strip()
        new_cell = ""
        while cell is not "":
            found = False

            for value in self.valid_list:
                if cell.startswith(value):
                    found = True
                    new_cell += value + "\n"
                    cell = cell[len(value) :]
                if cell.startswith(","):
                    cell = cell[1:]

            if not found:
                raise Exception("Could not find valid value in " + cell)

            cell = cell.strip()

        return new_cell.strip()


class AnnualBudget(Enum):
    LESS_THAN_1_MIL = "Less than $1 Million"
    BETWEEN_1_MIL_AND_5_MIL = "$1 to $5 Million"
    BETWEEN_5_MIL_AND_10_MIL = "$5 to $10 Million"
    BETWEEN_10_MIL_AND_25_MIL = "$10 to $25 Million"
    BETWEEN_25_MIL_AND_50_MIL = "$25 to $50 Million"
    BETWEEN_50_MIL_AND_100_MIL = "$50 to $100 Million"
    BETWEEN_100_MIL_AND_500_MIL = "$100 to $500 Million"
    BETWEEN_500_MIL_AND_1_BIL = "$500 Million to $1 Billion"
    MORE_THAN_1_BIL = "$1 Billion +"


class AnnualBudgetProcessor(CellProcessor):
    """Normalizes the Annual Budget, so that a unified (GlobalView) TOC
    works across competitions.

    Requires, as input, a map where the keys are options in the AnnualBudget enum."""

    def __init__(self, mapping):
        # We invert the mapping for lookup as we process the cell, but we want
        # the external interface to make more sense and keeping the enum
        # as the key makes the client look nicer.
        self.reverse_mapping = {v: k for k, v in mapping.items()}

    def process_cell(self, proposal, column_name):
        cell = proposal.cell(column_name)
        if cell not in self.reverse_mapping:
            raise Exception("%s is not a configured budget value" % cell)

        return self.reverse_mapping[cell].value


class SustainableDevelopmentGoalProcessor(CellProcessor):
    """Normalizes the Sustainable Development Goals.  The list from
    1-17 for the text of the competition should get passed in.  The
    official list can be found at
    https://en.wikipedia.org/wiki/Sustainable_Development_Goals"""

    official_sdgs = [
        "No Poverty",
        "Zero Hunger",
        "Good Health and Well-being",
        "Quality Education",
        "Gender Equality",
        "Clean Water and Sanitation",
        "Affordable and Clean Energy",
        "Decent Work and Economic Growth",
        "Industry, Innovation and Infrastructure",
        "Reduced Inequality",
        "Sustainable Cities and Communities",
        "Responsible Consumption and Production",
        "Climate Action",
        "Life Below Water",
        "Life on Land",
        "Peace, Justice and Strong Institutions",
        "Partnerships for the Goals",
    ]

    def __init__(self, sdg_list):
        self.reverse_mapping = {v: idx for idx, v in enumerate(sdg_list)}

    def process_cell(self, proposal, column_name):
        cell = proposal.cell(column_name)

        new_cell = ""
        for value in cell.split("\n"):
            if value not in self.reverse_mapping.keys():
                raise Exception("'%s' is not a configured sdg value" % value)

            new_cell += self.official_sdgs[self.reverse_mapping[value]] + "\n"

        return new_cell.strip()


class BudgetTableProcessor(CellProcessor):
    """A CellProcessor specifically for the Budget Table format sent
    from Common Pool, that then gets uploaded as a json document for
    torque to work with."""

    def column_type(self):
        return "json"

    def process_cell(self, proposal, column_name):
        cell = proposal.cell(column_name)
        budget_rows = cell.split("||")
        budget_row_data = []
        for budget_row in budget_rows:
            budget_items = budget_row.split("|")
            budget_amount = utils.commaize_number(budget_items[1])
            budget_row_data.append(
                {"description": budget_items[0], "amount": budget_amount}
            )
        return json.dumps(budget_row_data)


class NumberCommaizer(CellProcessor):
    """A CellProcessor that takes large numbers and inserts commas where appropriate,
    and does nothing if it looks like they aren't large numbers."""

    def column_type(self):
        return None

    def process_cell(self, proposal, column_name):
        """Return the CELL with commas as if it were a large number,
        or do nothing if not parseable as a number"""

        return utils.commaize_number(proposal.cell(column_name))


class CorrectionData(CellProcessor):
    """A CellProcessor that's generated from a csv file that has a row
    per proposal (keyed by the specified KEY_COLUMN), and then columns for
    the data in that spreadsheet that's being overriden, if not empty.
    An example would look like:

    Review Number,Project Title,Organization,...
    1,New Title for 1,Corrected Organization,...
    2,Correct Title for 2,,...   # There is no entry for Organization,
                                 # so no correction is made

    Will then replace cells in the proposals with the updated version."""

    def __init__(self, key_column_name, correction_csv):
        self.correction_data = {}

        csv_reader = csv.reader(
            open(correction_csv, encoding="utf-8"), delimiter=",", quotechar='"'
        )
        self.header = next(csv_reader)
        key_col_idx = self.header.index(key_column_name)

        for correction_row in csv_reader:
            key = correction_row[key_col_idx]
            if key not in self.correction_data:
                self.correction_data[key] = {}
            for col_name, datum in zip(self.header, correction_row):
                # If empty, or the key column, don't correct
                if col_name != key_column_name and datum:
                    self.correction_data[key][col_name] = datum

    def columns_affected(self):
        """Get all the columns this correction file corrects.  This can
        be used with a loop to process a competition."""
        return self.header

    def column_type(self):
        return None

    def process_cell(self, proposal, column_name):
        key = proposal.key()
        if key in self.correction_data and column_name in self.correction_data[key]:
            return self.correction_data[key][column_name]

        return proposal.cell(column_name)


class ColumnTypeUpdater(CellProcessor):
    """This doesn't actually process the cell, but adds a column type
    of COLUMN_TYPE passed in, so that for cells that are already processed
    completely, we can add the type for the column"""

    def __init__(self, col_type):
        self.col_type = col_type

    def column_type(self):
        return self.col_type


class DefaultValueSetter(CellProcessor):
    """Sets the value to DEFAULT_VALUE if no value set there already."""

    def __init__(self, default_value):
        self.default_value = default_value

    def process_cell(self, proposal, column_name):
        return proposal.cell(column_name) or self.default_value


class InformationAdder:
    """The base class for things that add information to proposals that
    aren't in the base spreadsheet.  Will usually implement column_type,
    names, and cell"""

    def column_type(self, column_name):
        """Returns the column type for the COLUMN_NAME that would have
        been added by this adder"""
        return None

    def column_names(self):
        """Returns a list of column names that this adder will be adding
        to the competition"""
        return []

    def cell(self, proposal, column_name):
        """Returns the new cell for the proposal PROPOSAL denoted by
        COLUMN_NAME.  This is information generated by the Adder, but
        can use other information within the PROPOSAL."""
        pass


class LinkedSecondSheet(InformationAdder):
    """Adder in the case that there's a second sheet that has one proposal
    per row, like the original sheet, and has information that should
    get added."""

    def __init__(
        self,
        csv_location,
        key_column_name,
        additional_columns,
    ):
        """Builds the dataset from the CSV_LOCATION, using the KEY_COLUMN_NAME
        to link up against the proposal keys, and the adds the columns from
        ADDITIONAL_COLUMN

        ADDITIONAL_COLUMN is a list of objects of the form:
        {
          "source_name": a string, the name of the column in the linked sheet
          "target_name": a string, the name of the column as it should appear
                         in the final csv.  If omited, source_name is used
          "type": a string, the type of the column, optional
        }"""
        csv_reader = csv.reader(
            open(csv_location, encoding="utf-8"), delimiter=",", quotechar='"'
        )
        header_row = next(csv_reader)

        key_col_idx = header_row.index(key_column_name)
        self.additional_columns = additional_columns
        self.data = {}

        additional_columns = [
            {
                "source_name": col["source_name"],
                "target_name": col["target_name"]
                if "target_name" in col.keys()
                else col["source_name"],
                "type": col["type"] if "type" in col.keys() else None,
            }
            for col in additional_columns
        ]
        for row in csv_reader:
            self.data[row[key_col_idx]] = {
                col["target_name"]: row[header_row.index(col["source_name"])]
                for col in additional_columns
            }
        self.additional_column_types = {
            col["target_name"]: col["type"] for col in additional_columns
        }
        self.additional_column_names = [
            col["target_name"] for col in additional_columns
        ]

    def column_type(self, column_name):
        if column_name in self.additional_column_types.keys():
            return self.additional_column_types[column_name]
        return None

    def column_names(self):
        return self.additional_column_names

    def cell(self, proposal, column_name):
        if proposal.key() in self.data and column_name in self.data[proposal.key()]:
            return self.data[proposal.key()][column_name]
        elif proposal.cell(column_name):
            return proposal.cell(column_name)

        return ""


class MediaWikiTitleAdder(InformationAdder):
    """An InformationAdder that adds the MediaWiki Title column, which
    is a wiki safe version of "<Project Title> (<Application #>)"""

    title_column_name = "MediaWiki Title"

    def __init__(self, project_column_name):
        self.project_column_name = project_column_name

    def column_type(self, column_name):
        return None

    def column_names(self):
        return [self.title_column_name]

    def cell(self, proposal, column_name):
        title = "%s (%s)" % (proposal.cell(self.project_column_name), proposal.key())
        return self.sanitize_title(title)

    def sanitize_title(self, title):
        import unidecode

        # Project titles sometimes have characters that lead to malformed
        # mediawiki titles so this code cleans that up.
        for c in [
            "#",
            "<",
            ">",
            "[",
            "]",
            "{",
            "|",
            "}",
        ]:
            if title.find(c) != -1:
                title = title.replace(c, "-")
        while len(bytes(title, "UTF-8")) > 255:
            title = title[:-1]
        title = title.replace("\n", " ")

        # This line is just so our mediawiki title matches what actually happens
        # when the page is created in the wiki.  Needed for the wiki sanity checking
        title = title.replace("  ", " ")

        # All mediawiki titles are capitalized, so we lean into that
        title = title[0].upper() + title[1:]

        # Also convert non unicode because we do this with titles on the other side
        return unidecode.unidecode_expect_nonascii(title).strip()


class StaticColumnAdder(InformationAdder):
    """An InformationAdder that adds a column, and sets that column
    to a specific value for all rows of the sheet.  This is useful
    for meta information about a given sheet, so that when using
    a wiki that has more than one sheet (GlobalView), there's certain
    information that is constant for all proposals coming from that
    sheet"""

    def __init__(self, column_name, value):
        self.column_name = column_name
        self.value = value

    def column_type(self, column_name):
        return None

    def column_names(self):
        return [self.column_name]

    def cell(self, proposal, column_name):
        return self.value


class FinancialDataAdder(InformationAdder):
    """Adder that takes a FINANCIAL_SHEETS_DIR, filled with csvs named
    <Application #>.csv, as well as a DEFINITIONS dictionary that
    determines how those are converted into a "LFC Financial Data"
    field, of type json.  If the proposal number is not in the
    FINANCIAL_SHEETS_DIR, then the empty object will be passed up.

    The DEFINITIONS will be a list of definitions, of the form:

    {
        "name": String, the name in the eventual json
        "text": String, the text of the first column to match against
        "percent": Boolean, whether these numbers are percents or not.
                   Defaults to False
    }

    The csv coming in should be of the type:

    <ignored>,year1,year2,year3,...
    <item1>,val,val,val,...
    <item2>,val,val,val,...
    <item3>,val,val,val,...
    ,,,,
    Footnotes
    footnote1
    footnote2
    ...

    Where the <item>s match the definition "text" exactly, and there are N
    footnotes.

    The exporting format is of the form:

    {
       "years": Array, list of years
       "line_items": {
           "name": name mathing the "name" field in the DEFINITIONS (above)
           "data": Array of strings, list of Strings representing the data on those years
       }
       "footnoates": String, with a newline separated set of footnotes
    }"""

    def __init__(self, financial_sheets_dir, definitions):
        self.financial_data = {}

        for financial_csv_name in os.listdir(financial_sheets_dir):
            key = re.sub("\.csv$", "", financial_csv_name)
            financial_csv_file = os.path.join(financial_sheets_dir, financial_csv_name)

            proposal_financial_data = {}

            reader = csv.reader(
                open(financial_csv_file),
                delimiter=",",
                quotechar='"',
                lineterminator="\n",
            )

            header = next(reader)
            proposal_financial_data["years"] = [year for year in header[1:] if year]

            proposal_financial_data["line_items"] = []
            hit_footnotes = False
            for row in reader:
                if len(row) == 0 or not row[0] or row[0].lower() == "footnotes":
                    hit_footnotes = True
                    break

                item_string = row[0]
                definition = None

                for defi in definitions:
                    if defi["text"] == item_string.strip():
                        definition = defi

                if definition is None:
                    raise Exception(
                        "Can't find definition for '%s'.  Aborting." % item_string
                    )

                # This is some serious special casing to recreate the formatting in xlsx
                items = []
                for item in row[1 : len(proposal_financial_data["years"]) + 1]:
                    try:
                        float_item = float(item)
                        if "percent" in definition and definition["percent"]:
                            float_item_str = "{:.2f}%".format(abs(float_item) * 100)
                        else:
                            float_item_str = "{:.2f}".format(abs(float_item))

                        if float_item < 0:
                            items.append("({})".format(float_item_str))
                        else:
                            items.append(float_item_str)
                    except ValueError:
                        items.append(item)

                line_item = {"name": definition["name"], "items": items}
                proposal_financial_data["line_items"].append(line_item)

            if not hit_footnotes:
                for row in reader:
                    if len(row) > 0 and row[0] == "Footnotes":
                        break

            footnotes = ""
            for row in reader:
                if len(row) > 0 and row[0]:
                    footnotes += utils.fix_cell(row[0] + "\n")

            proposal_financial_data["footnotes"] = footnotes

            self.financial_data[key] = proposal_financial_data

    def column_type(self, column_name):
        return "json"

    def column_names(self):
        return ["LFC Financial Data"]

    def cell(self, proposal, column_name):
        return json.dumps(self.financial_data.get(proposal.key(), {}))


class GlobalViewMediaWikiTitleAdder(MediaWikiTitleAdder):
    """A MediaWikiTitleAdder that has a different title layout because it's tailored
    to GlobalView, so that it contains the independent competition sheet name."""

    def __init__(self, wiki_key, project_column_name):
        self.project_column_name = project_column_name
        self.wiki_key = wiki_key

    def column_names(self):
        return ["GlobalView MediaWiki Title"]

    def cell(self, proposal, column_name):
        title = "%s (%s: %s)" % (
            proposal.cell(self.project_column_name),
            self.wiki_key,
            proposal.key(),
        )
        return self.sanitize_title(title)


@total_ordering
class Attachment:
    """Represents an attachment on the file system, and handles special cases
    about display names to make sure things show up correctly"""

    def __init__(self, key, filename, column_name, path):
        self.file = filename
        self.rank = None
        self.key = key
        self.path = path
        self.column_name = column_name
        self.name = re.sub("^\\d*_", "", filename)
        self.name = re.sub("\.pdf$", "", self.name)
        if len(self.name) > 33:
            self.name = self.name[0:15] + "..." + self.name[(len(self.name) - 15) :]

    def __eq__(self, other):
        return self.rank == other.rank and self.name == other.name

    def __ne__(self, other):
        return self.rank != other.rank or self.name != other.name

    def __gt__(self, other):
        if self.rank is other.rank:
            return self.name > other.name

        # Sort unranked things to the bottom
        if self.rank is None:
            return True

        if other.rank is None:
            return False

        return self.rank > other.rank


class BasicAttachments(InformationAdder):
    """Represents a set of attachments generated from an ATTACHMENT_DIR provided
    at initialization.  These attachments can later be pulled out to upload to
    MediaWiki, but also is an InformationAdder so that those attachments values
    are in the Proposal so that torque knows where they are.

    The KEYS passed in the constructor refers to which proposals to look for
    attachments in, as the ATTACHMENTS_DIR should always have subdirectories
    per proposal by key.

    The column names can be variable based on what attachments are important
    for the competition.

    When rank is unset, attachments move to the end."""

    defined_column_names = ["Attachment Display Names", "Attachments"]

    def __init__(self, keys, attachments_dir):
        self.attachments = []

        # Attachments are always in a directory structure of
        # <attachments_dir>/<application #>/*
        if attachments_dir is not None and os.path.isdir(attachments_dir):
            for key in keys:
                if not os.path.isdir(os.path.join(attachments_dir, key)):
                    continue

                if not re.search("^\\d*$", key):
                    continue

                full_application_attachment_dir = os.path.join(attachments_dir, key)
                for attachment_file in os.listdir(full_application_attachment_dir):
                    if os.path.isdir(
                        os.path.join(attachments_dir, key, attachment_file)
                    ):
                        continue

                    if re.search("^\\d*_Registration.pdf", attachment_file):
                        continue

                    self.attachments.append(
                        Attachment(
                            key,
                            attachment_file,
                            BasicAttachments.defined_column_names[1],
                            os.path.join(
                                full_application_attachment_dir, attachment_file
                            ),
                        )
                    )

    def column_type(self, column_name):
        # List for both, so we don't need to switch on it
        if column_name in self.defined_column_names:
            return "list"
        return None

    def column_names(self):
        return BasicAttachments.defined_column_names

    def cell(self, proposal, column_name):
        attachments = [a for a in self.attachments if a.key == proposal.key()]
        attachments.sort()

        attachments_by_column_name = {name: [] for name in self.defined_column_names}
        for attachment in attachments:
            if attachment.column_name not in attachments_by_column_name:
                attachments_by_column_name[attachment.column_name] = []
            attachments_by_column_name[attachment.column_name].append(attachment)

        if column_name == self.defined_column_names[0]:
            return "\n".join(
                [
                    a.name
                    for a in attachments_by_column_name[self.defined_column_names[1]]
                ]
            )
        elif column_name == self.defined_column_names[1]:
            return "\n".join(
                [
                    a.file
                    for a in attachments_by_column_name[self.defined_column_names[1]]
                ]
            )
        elif column_name in attachments_by_column_name:
            return "\n".join([a.file for a in attachments_by_column_name[column_name]])
        else:
            return ""


class RegexSpecifiedAttachments(BasicAttachments):
    """A special case of BasicAttachments with the ability to specify the name
    and the rank based on a regular expression using the method SPECIFY_BY_REGEX.

    The option to add a new column to the sheet specifically for the attachment
    also exists using specify_new_column."""

    def __init__(self, keys, attachments_dir):
        super().__init__(keys, attachments_dir)
        self.nonlist_columns = []
        self.list_columns = []

    def column_type(self, column_name):
        if column_name in self.defined_column_names + self.list_columns:
            return "list"
        return None

    def column_names(self):
        return (
            BasicAttachments.defined_column_names
            + self.nonlist_columns
            + self.list_columns
        )

    def specify_by_regex(self, regex, name, rank=None):
        """Matches the REGEX against the filename, and then updates the display
        name to NAME, and the rank to RANK (default of None, or last) if it matches."""
        for attachment in self.attachments:
            if re.search(regex, attachment.file, flags=re.I):
                attachment.name = name
                attachment.rank = rank

    def specify_new_column(self, regex, column_name, rank=None, is_list=False):
        """Matches the REGEX against the filename, and then updates the display
        name to COLUMN_NAME, and the rank to RANK (default of None, or last) if it matches.

        Also adds COLUMN_NAME as a a column to the spreadsheet and links the
        attachments specified to that column"""

        if is_list:
            self.list_columns.append(column_name)
        else:
            self.nonlist_columns.append(column_name)
        for attachment in self.attachments:
            if re.search(regex, attachment.file, flags=re.I):
                attachment.rank = rank
                attachment.column_name = column_name


class AdminReview(InformationAdder, ProposalFilter):
    """Adds the result of the Admin Review spreadsheets into a column "Valid",
    and is also a filter for proposals that don't show up in that spreadsheet."""

    def __init__(self, csv_location, key_column_name, valid_column_name):
        """Builds the dataset from the CSV_LOCATION, using the KEY_COLUMN_NAME
        to link up against the proposal keys, and the VALID_COLUMN_NAME for
        which column in the admin spreadsheet has the validity column"""
        csv_reader = csv.reader(
            open(csv_location, encoding="utf-8"), delimiter=",", quotechar='"'
        )
        header_row = next(csv_reader)

        key_col_idx = header_row.index(key_column_name)
        valid_col_idx = header_row.index(valid_column_name)
        self.data = {row[key_col_idx]: row[valid_col_idx] for row in csv_reader}

    def column_type(self, column_name):
        return None

    def column_names(self):
        return ["Valid"]

    def cell(self, proposal, column_name):
        return self.data[proposal.key()] if (proposal.key() in self.data) else ""

    def filter_proposal(self, proposal):
        return proposal.key() not in self.data


class EvaluationRankingsAdder(InformationAdder):
    """Represents the first pass of review data we get that has just the scores
    avaliable, without the comments.  Usually superseded later by using the
    EvaluationAdder with a sheet that has all the comments and score breakdowns as
    well.

    Each row represents a proposal with the scores in their own columns"""

    def __init__(
        self,
        csv_location,
        name,
        app_col_name,
        overall_rank_col_name,
        score_total_col_name,
        trait_defs,
    ):
        """Takes a CSV_LOCATION, reading the data about proposal based on
        APP_COL_NAME, and associating with the data in OVERALL_RANK_COL_NAME,
        and SOCRE_TOTAL_NAME.

        The NAME represents the type of evaluation data (Judge, Peer Review, etc).

        TRAIT_DEFS is an array of dictionaries of the form:

        TRAIT_DEF = {
          NAME: string, the name of the trait as it will appear in the output
          SOURCE_COL_NAME: string, representing the column name in the source spreadsheet
        }"""

        csv_reader = csv.reader(
            open(csv_location, encoding="utf-8"), delimiter=",", quotechar='"'
        )

        self.name = name
        self.traits = []
        self.evaluation_data = {}

        header_row = next(csv_reader)

        app_col = header_row.index(app_col_name)
        overall_rank_col = header_row.index(overall_rank_col_name)
        score_total_col = header_row.index(score_total_col_name)

        for trait_def in trait_defs:
            self.traits.append(trait_def["name"])
            trait_def["col"] = header_row.index(trait_def["source_col_name"])

        for row in csv_reader:
            application_id = row[app_col]

            evaluation_datum = {
                "{} Overall Score Rank Normalized".format(self.name): row[
                    overall_rank_col
                ],
                "{} Sum of Scores Normalized".format(self.name): row[score_total_col],
            }

            for trait_def in trait_defs:
                evaluation_datum[
                    "{} {}".format(self.name, trait_def["name"])
                ] = trait_def["name"]
                evaluation_datum[
                    "{} {} Score Normalized".format(self.name, trait_def["name"])
                ] = row[trait_def["col"]]

            self.evaluation_data[application_id] = evaluation_datum

    def column_names(self):
        names = [
            "{} Overall Score Rank Normalized".format(self.name),
            "{} Sum of Scores Normalized".format(self.name),
        ]
        names.extend(["{} {}".format(self.name, trait) for trait in self.traits])
        names.extend(
            ["{} {} Score Normalized".format(self.name, trait) for trait in self.traits]
        )

        return names

    def cell(self, proposal, column_name):
        if proposal.key() not in self.evaluation_data:
            if column_name == "%s Overall Score Rank Normalized" % self.name:
                return "9999"
            return ""

        val = self.evaluation_data[proposal.key()][column_name]

        if isinstance(val, float):
            return "{0:.1f}".format(val)
        else:
            return val


class EvaluationAdder(InformationAdder):
    """Reperesents the evaluation data that comes in from a many to one relationship
    to the proposals.  There are N traits, and M judges per trait, with things like
    overall_score_rank_normalized being duplicated for all NxM rows."""

    def __init__(
        *params,
        app_col_name,
        score_rank_normalized_col_name,
        sum_of_scores_normalized_col_name,
        trait_col_name,
        score_normalized_col_name,
        comments_col_name,
        comments_score_normalized_col_name
    ):
        """Takes a NAME representing the name of this evaluation data (Judge, Peer Review, etc)
        and CSV_READER representing evaluation data in a spreadsheet and turns that into a dict
        of dicts in the following form:

          EVALUATION_DATA[app_id] = {
            overall_score_rank_normalized: string,
            sum_of_scores_normalized: string,
            traits: array of TRAIT (below)
          }

          TRAIT = {
            name: string,
            score_normalized: string
            comments: concatenated string, ready for list type
            comment_scores: concatenated string, ready for list type
          }

        The columns that data is looked up are required named integer arguments as follows:
          - APP_COL: column with application number
          - SCORE_RANK_NORMALIZED_COL: column with normalized score rank
          - SUM_OF_SCORES_NORMALIZED_COL: column with normalized scores
          - TRAIT_COL: column with the trait name
          - SCORE_NORMALIZED_COL: column with the normalized score
          - COMMENTS_COL: column with the comments
          - COMMENTS_SCORE_NORMALIZED_COL: the normalized score of the commeng

        The scores for the traits are added up based here rather than in the
        spreasheet.  Then, comments are concatenated for that trait.

        The following columns are added:
          - <NAME> Overall Score Rank Normalized
          - <NAME> Sum of Scores Normalized
          - Then for each unique TRAIT in the TRAIT_COL
            - <NAME> <TRAIT>
            - <NAME> <TRAIT> Comments
            - <NAME> <TRAIT> Score Normalized
            - <NAME> <TRAIT> Comment Scores Normalized
        """

        self = params[0]
        self.name = params[1]
        csv_location = params[2]

        csv_reader = csv.reader(
            open(csv_location, encoding="utf-8"), delimiter=",", quotechar='"'
        )

        self.traits = []
        self.evaluation_data = {}

        header_row = next(csv_reader)

        app_col = header_row.index(app_col_name)
        score_rank_normalized_col = header_row.index(score_rank_normalized_col_name)
        sum_of_scores_normalized_col = header_row.index(
            sum_of_scores_normalized_col_name
        )
        trait_col = header_row.index(trait_col_name)
        score_normalized_col = header_row.index(score_normalized_col_name)
        comments_col = header_row.index(comments_col_name)
        comments_score_normalized_col = header_row.index(
            comments_score_normalized_col_name
        )

        for row in csv_reader:
            application_id = row[app_col]
            if not application_id in self.evaluation_data:
                self.evaluation_data[application_id] = {
                    "%s Overall Score Rank Normalized"
                    % self.name: row[score_rank_normalized_col],
                    "%s Sum of Scores Normalized"
                    % self.name: row[sum_of_scores_normalized_col],
                }

            evaluation_datum = self.evaluation_data[application_id]

            trait_name = row[trait_col].strip()
            if trait_name not in self.traits:
                self.traits.append(trait_name)

            if "%s %s" % (self.name, trait_name) not in evaluation_datum:
                evaluation_datum["%s %s" % (self.name, trait_name)] = trait_name
                evaluation_datum[
                    "%s %s Score Normalized" % (self.name, trait_name)
                ] = 0.0
                evaluation_datum["%s %s Comments" % (self.name, trait_name)] = ""
                evaluation_datum[
                    "%s %s Comment Scores Normalized" % (self.name, trait_name)
                ] = ""

            evaluation_datum[
                "%s %s Score Normalized" % (self.name, trait_name)
            ] += float(row[score_normalized_col])
            evaluation_datum["%s %s Comments" % (self.name, trait_name)] += (
                utils.fix_cell(row[comments_col].replace("\n", "")) + "\n"
            )
            evaluation_datum[
                "%s %s Comment Scores Normalized" % (self.name, trait_name)
            ] += (row[comments_score_normalized_col] + "\n")

        self.traits.sort()

        self.regular_columns = [
            "%s Overall Score Rank Normalized" % self.name,
            "%s Sum of Scores Normalized" % self.name,
        ]
        self.regular_columns.extend(
            ["%s %s" % (self.name, trait) for trait in self.traits]
        )
        self.regular_columns.extend(
            ["%s %s Score Normalized" % (self.name, trait) for trait in self.traits]
        )
        self.list_columns = []
        self.list_columns.extend(
            ["%s %s Comments" % (self.name, trait) for trait in self.traits]
        )
        self.list_columns.extend(
            [
                "%s %s Comment Scores Normalized" % (self.name, trait)
                for trait in self.traits
            ]
        )

    def column_type(self, column_name):
        if column_name in self.list_columns:
            return "list"
        return None

    def column_names(self):
        return self.regular_columns + self.list_columns

    def cell(self, proposal, column_name):
        if proposal.key() not in self.evaluation_data:
            if column_name == "%s Overall Score Rank Normalized" % self.name:
                return "9999"
            return ""

        val = self.evaluation_data[proposal.key()][column_name]

        if isinstance(val, float):
            return "{0:.1f}".format(val)
        else:
            return val.strip()

class GeocodeAdder(InformationAdder):
    """Converts a specified set of address columns into geocode JSON columns."""

    def __init__(
        self,
        new_column_name,
        address_pattern,
        geocoder,
    ):
        """Takes:
        1. The name of the new column.
        2. A method that takes a proposal and returns the address to be geocoded.
        2. An instantiated Geocoder object.
        """
        self.new_column_name = new_column_name
        self.address_pattern = address_pattern
        self.geocoder = geocoder

    def column_names(self):
        return [self.new_column_name]

    def cell(self, proposal, column_name):
        address_pattern = self.address_pattern
        full_address = address_pattern(proposal)
        if (full_address == ''):
            return ""

        try:
            geocode_result = self.geocoder.geocode(full_address)
            if (geocode_result is None):
                print(f"COULD NOT GEOCODE: {full_address}")
            else:
                print(f"GEOCODED: {full_address}")
                return f"{geocode_result.latitude},{geocode_result.longitude}"
        except Exception as e:
            print(f"Error Geocoding: {full_address}")
            print(e)

        return ""
