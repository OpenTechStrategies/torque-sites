from etl import utils
from etl import Geocoder
import csv
import json
import os
import re
import sys
from functools import total_ordering
from enum import Enum


class Competition:
    """A Competition, encapsulating a set of Proposal objects"""

    def __init__(
        self,
        proposals,
        columns,
        sorted_proposal_keys,
        name,
        key_column_name,
    ):
        """Initializes the competition from PROPOSALS, with the sorted keys
        in SORTED_PROPOSAL_KEYS.  COLUMNS is the columns for those proposals.

        NAME refers to the name of the competition, KEY_COLUMN_NAME
        is which column in the base csv holds the identifier for the proposal."""

        self.name = name
        self.columns = columns
        self.key_column_name = key_column_name
        self.proposals = proposals
        self.sorted_proposal_keys = sorted_proposal_keys
        self.tocs = []
        self.allowlist_exceptions = []

    def process_all_cells_special(self, processor):
        """For all cells in the competition, apply CellProcessor PROCESSOR
        to them"""
        for column_name in self.columns:
            self.process_cells_special(column_name, processor)

    def process_cells_special(self, column_name, processor):
        """For cells in the competition at COLUMN_NAME,
        apply the PROCESSOR to them.  PROCESSOR is an object
        of the CellProcessor type."""
        for proposal in self.proposals.values():
            proposal.process_cell_special(column_name, processor)

    def add_supplemental_information(self, adder):
        """Adds additional columns to the competition via ADDER.  ADDER
        must be of the InformationAdder type.  This will add the
        headers and the data."""
        for column_name in adder.column_names():
            # Even though this is meant for adding columns, there are times
            # when adding overwrites columns, such as when merging two sheets
            # together.
            if column_name not in self.columns:
                self.columns.append(column_name)

            for proposal in self.proposals.values():
                proposal.add_cell(column_name, adder.cell(proposal, column_name))

    def remove_information(self, remover):
        """Removes columns from a sheet via REMOVER.  REMOVER must
        be of the InformationRemover type."""
        for column_name in remover.columns_to_remove():
            if column_name in self.columns:
                self.columns.remove(column_name)
            else:
                raise Exception("Column %s is not in our column list" % column_name)

            for proposal in self.proposals.values():
                proposal.remove_cell(column_name)

    def transform_sheet(self, transformer):
        """Transforms the sheet via TRANSFORMER.  TRANSFORMER must
        be of the InformationTransformer type.  This will first
        call the add methods, then the remove methods.

        This method is not for transforming the information in the sheet,
        but rather transforming the structure of it.  You should use
        PROCESS_CELLS_SPECIAL for information change.
        """
        self.add_supplemental_information(transformer)
        self.remove_information(transformer)

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

    def to_json(self, output):
        """Writes a json document out to stream OUTPUT designed to be uploaded to a
        torque instance"""
        output.write(
            json.dumps([p.to_dict(self.columns) for p in self.ordered_proposals()])
        )
        return output

    def add_toc(self, toc):
        """Adds a toc.Toc to this competition."""
        self.tocs.append(toc)

    def process_tocs(self):
        """Processes all the tocs.  Usually should be done after the
        competition is completely assembled."""
        for toc in self.tocs:
            toc.process_competition(self)

    def add_allowlist_exception(self, column_name, column_group):
        """Adds COLUMN_NAME to the list of fields that aren't errored on, even
        if it isn't in the allowlist."""
        self.allowlist_exceptions.append((column_name, column_group))

    def validate_fields(self):
        """Validate that all the fields being uploaded are in the allowlist"""
        from etl import field_allowlist

        # Flattens the lists
        allowlisted_fields = [
            f for fieldlist in field_allowlist.allowlist.values() for f in fieldlist
        ]
        exceptions = [f for (f, g) in self.allowlist_exceptions]

        passed_allowlist = True
        for column in self.columns:
            if column not in allowlisted_fields and column not in exceptions:
                passed_allowlist = False
                print("Column '%s' is not in allowlisted fields file" % column)

        if not passed_allowlist:
            raise Exception("Did not pass allowlist, see above for why")

    def rekey(self, new_column_name):
        """Sometimes the key column is one of the ones that has changed or been combined, in which
        case, after that update, we need to rekey the whole competition to the new name"""
        self.key_column_name = new_column_name
        for proposal in self.proposals.values():
            proposal.key_column_name = new_column_name


class CsvBasedCompetition(Competition):
    """A Competition that's based on a master CSV, usually from outside sources."""

    def __init__(
        self,
        proposals_location,
        name,
        key_column_name,
        pare=None,
    ):
        """Initializes the competition from the source spreadsheet in
        PROPOSALS_LOCATION (a file location).  Loads up the CSV and processes
        it.

        NAME refers to the name of the competition, KEY_COLUMN_NAME
        is which column in the base csv holds the identifier for the proposal.

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

        # We strip out \ufeff here because sometimes the spreadsheets we get
        # are edited by macs, and that adds this extra character, which messes
        # up our columns!
        columns = [col.strip().replace("\ufeff", "") for col in next(proposals_reader)]
        proposals = {}
        sorted_proposal_keys = []

        row_num = 0
        key_column_idx = columns.index(key_column_name)
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

            proposal = Proposal(dict(zip(columns, row)), key_column_name)
            key = proposal.key()
            proposals[key] = proposal
            sorted_proposal_keys.append(key)

        super().__init__(
            proposals, columns, sorted_proposal_keys, name, key_column_name
        )


class JsonBasedCompetition(Competition):
    """A Competition that's based on a master JSON, usually generated from other competition etl pipelines."""

    def __init__(
        self,
        proposals_location,
        name,
        key_column_name,
        pare=None,
    ):
        """Initializes the competition from the source json file in
        PROPOSALS_LOCATION (a file location).

        NAME refers to the name of the competition, KEY_COLUMN_NAME
        is which column in the base csv holds the identifier for the proposal.

        PARE, when passed in, restricts the number of items as defined by utils.parse_pare"""
        proposal_data = json.load(open(proposals_location, encoding="utf-8"))

        if len(proposal_data) == 0:
            raise Exception("Proposal data was empty, which means we can't get columns")

        columns = list(proposal_data[0].keys())

        proposals = {}
        sorted_proposal_keys = []

        row_num = 0
        pare_factor, keys_to_include = utils.parse_pare(pare)
        for proposal_datum in proposal_data:
            row_num = row_num + 1
            if pare_factor is not None and (row_num % pare_factor) != 0:
                continue

            if (
                keys_to_include is not None
                and proposal[key_column_name] not in keys_to_include
            ):
                continue

            proposal = Proposal(proposal_datum, key_column_name)
            key = proposal.key()
            proposals[key] = proposal
            sorted_proposal_keys.append(key)

        super().__init__(
            proposals, columns, sorted_proposal_keys, name, key_column_name
        )


class Proposal:
    """A Proposal, of which there are many in a competition.  A Proposal
    loosely represents one row in the master spreadsheet, but provides
    indexing based on names, ability to add new fields, etc"""

    def __init__(self, data, key_column_name):
        """DATA is a dictionary of the proposal initial data.
        KEY_COLUMN_NAME is used to later get the key of this proposal.

        This sets up the proposal by processing the initial row"""
        self.data = data
        self.key_column_name = key_column_name

    def add_cell(self, column_name, cell):
        """Adds a new value CELL to the place held by COLUMN_NAME"""
        self.data[column_name] = cell

    def remove_cell(self, column_name):
        """Removes the information held by COLUMN_NAME"""
        del self.data[column_name]

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

    def to_dict(self, column_names):
        """Transforms this Proposal into an array for output, ordered by
        COLUMN_NAMES"""
        return {column_name: self.cell(column_name) for column_name in column_names}


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
    """The base class for Cell Processors, which implement process_cell"""

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


class ToListProcessor(CellProcessor):
    """A CellProcessor that splits a cell on the initialized SPLIT_STRING
    (defautling to comma: ",") into a list."""

    def __init__(self, split_string=","):
        self.split_string = split_string

    def process_cell(self, proposal, column_name):
        cell = proposal.cell(column_name)
        return [elem.strip() for elem in cell.split(self.split_string)]


class ToSpecifiedListProcessor(CellProcessor):
    """A CellProcesor that splits a cell into a list, but does
    so based on a passed in list, verifying that each item appears
    in the specified list, and allowing items to have commas in them."""

    def __init__(self, valid_list):
        self.valid_list = valid_list

    def process_cell(self, proposal, column_name):
        cell = proposal.cell(column_name).strip()
        processed_value = []
        while cell != "":
            found = False

            for value in self.valid_list:
                if cell.startswith(value):
                    found = True
                    processed_value.append(value)
                    cell = cell[len(value) :]
                if cell.startswith(","):
                    cell = cell[1:]

            if not found:
                raise Exception("Could not find valid value in " + cell)

            cell = cell.strip()

        return processed_value


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

        new_cell = []
        for value in cell:
            if value not in self.reverse_mapping.keys():
                raise Exception("'%s' is not a configured sdg value" % value)

            new_cell.append(self.official_sdgs[self.reverse_mapping[value]])

        return new_cell


class BudgetTableProcessor(CellProcessor):
    """A CellProcessor specifically for the Budget Table format sent
    from Common Pool, that then gets uploaded as a json document for
    torque to work with."""

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
        return budget_row_data


class NumberCommaizer(CellProcessor):
    """A CellProcessor that takes large numbers and inserts commas where appropriate,
    and does nothing if it looks like they aren't large numbers."""

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

    def process_cell(self, proposal, column_name):
        key = proposal.key()
        if key in self.correction_data and column_name in self.correction_data[key]:
            return self.correction_data[key][column_name]

        return proposal.cell(column_name)


class DefaultValueSetter(CellProcessor):
    """Sets the value to DEFAULT_VALUE if no value set there already."""

    def __init__(self, default_value):
        self.default_value = default_value

    def process_cell(self, proposal, column_name):
        return proposal.cell(column_name) or self.default_value


class InformationRemover:
    """The base class for things that remove information from proposals.
    Sometimes, extra columns come from the base sheet that don't need
    to be uploaded.  In the past, we just ignored them, but it's cleaner
    to remove them from the uploaded information."""

    def columns_to_remove(self):
        """Returns a list of columns to remove"""
        return []


class InformationAdder:
    """The base class for things that add information to proposals that
    aren't in the base spreadsheet.  Will usually implement column_names, and cell"""

    def column_names(self):
        """Returns a list of column names that this adder will be adding
        to the competition"""
        return []

    def cell(self, proposal, column_name):
        """Returns the new cell for the proposal PROPOSAL denoted by
        COLUMN_NAME.  This is information generated by the Adder, but
        can use other information within the PROPOSAL."""
        pass


class InformationTransformer(InformationAdder, InformationRemover):
    """Transforms the sheet by first adding information, and then removing
    information."""

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
        self.additional_column_names = [
            col["target_name"] for col in additional_columns
        ]

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

    def column_names(self):
        return ["LFC Financial Data"]

    def cell(self, proposal, column_name):
        return self.financial_data.get(proposal.key(), {})


class GlobalViewMediaWikiTitleAdder(MediaWikiTitleAdder):
    """A MediaWikiTitleAdder that has a different title layout because it's tailored
    to GlobalView, so that it contains the independent competition sheet name."""

    title_column_name = "GlobalView MediaWiki Title"

    def __init__(self, wiki_key, project_column_name):
        self.project_column_name = project_column_name
        self.wiki_key = wiki_key

    def column_names(self):
        return [self.title_column_name]

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

    def __init__(self, key, filename, column_name, subcolumn_name, path):
        self.file = filename
        self.rank = None
        self.key = key
        self.path = path
        self.column_name = column_name
        self.subcolumn_name = subcolumn_name
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

    BASIC_COLUMN_NAME = "Attachments"
    RESTRICTED_COLUMN_NAME = "Restricted Attachments"

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
                            BasicAttachments.BASIC_COLUMN_NAME,
                            "Default",
                            os.path.join(
                                full_application_attachment_dir, attachment_file
                            ),
                        )
                    )

    def column_names(self):
        return [
            BasicAttachments.BASIC_COLUMN_NAME,
            BasicAttachments.RESTRICTED_COLUMN_NAME,
        ]

    def cell(self, proposal, column_name):
        attachments = [a for a in self.attachments if a.key == proposal.key()]
        attachments.sort()

        by_column_name = {
            BasicAttachments.BASIC_COLUMN_NAME: {},
            BasicAttachments.RESTRICTED_COLUMN_NAME: {},
        }

        for attachment in attachments:
            if attachment.column_name not in by_column_name:
                raise Exception(
                    "Attachment not in a valid column name: %s" % attachment.column_name
                )

            if attachment.subcolumn_name not in by_column_name[attachment.column_name]:
                by_column_name[attachment.column_name][attachment.subcolumn_name] = []

            by_column_name[attachment.column_name][attachment.subcolumn_name].append(
                {"file": attachment.file, "name": attachment.name}
            )

        return by_column_name[column_name]


class RegexSpecifiedAttachments(BasicAttachments):
    """A special case of BasicAttachments with the ability to specify the name
    and the rank based on a regular expression using the method SPECIFY_BY_REGEX.

    The option to add a new column to the sheet specifically for the attachment
    also exists using specify_new_column."""

    def __init__(self, keys, attachments_dir):
        super().__init__(keys, attachments_dir)

    def specify_by_regex(self, regex, name, rank=None):
        """Matches the REGEX against the filename, and then updates the display
        name to NAME, and the rank to RANK (default of None, or last) if it matches."""
        for attachment in self.attachments:
            if re.search(regex, attachment.file, flags=re.I):
                attachment.name = name
                attachment.rank = rank

    def specify_new_subcolumn(self, regex, column_name, rank=None):
        """Matches the REGEX against the filename, and then updates the display
        name to COLUMN_NAME, and the rank to RANK (default of None, or last) if it matches.

        Also updates the subcolumn of the attachment to COLUMN_NAME"""

        for attachment in self.attachments:
            if re.search(regex, attachment.file, flags=re.I):
                attachment.rank = rank
                attachment.subcolumn_name = column_name


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

    def column_names(self):
        return ["Admin Review Status"]

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
        primary_rank,
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
        self.primary_rank = primary_rank

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
                "{} Score".format(self.name): {
                    "Normalized": row[score_total_col],
                },
                "{} Rank".format(self.name): {
                    "Normalized": row[overall_rank_col],
                }
            }

            if primary_rank:
                evaluation_datum["Rank"] = row[overall_rank_col]

            for trait_def in trait_defs:
                evaluation_datum["{} {} Score".format(self.name, trait_def["name"])] = {
                    "Normalized": row[trait_def["col"]]
                }

            self.evaluation_data[application_id] = evaluation_datum

    def column_names(self):
        names = [
            "{} Score".format(self.name),
            "{} Rank".format(self.name),
        ]
        names.extend(["{} {} Score".format(self.name, trait) for trait in self.traits])

        if self.primary_rank:
            names.append("Rank")

        return names

    def cell(self, proposal, column_name):
        if proposal.key() not in self.evaluation_data:
            if column_name == "Rank":
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
        score_rank_raw_col_name,
        score_rank_normalized_col_name,
        sum_of_scores_raw_col_name,
        sum_of_scores_normalized_col_name,
        trait_col_name,
        score_raw_col_name,
        score_normalized_col_name,
        comments_col_name,
        comments_score_raw_col_name,
        comments_score_normalized_col_name,
        anonymous_judge_name_col_name,
        primary_rank,
    ):
        """Takes a NAME representing the name of this evaluation data (Judge, Peer Review, etc)
        and CSV_READER representing evaluation data in a spreadsheet and turns that into a dict
        of dicts in the following form:

        The columns that data is looked up are required named integer arguments as follows:
          - APP_COL_NAME: column with application number
          - SCORE_RANK_RAW_COL_NAME: column with score rank
          - SCORE_RANK_NORMALIZED_COL_NAME: column with normalized score rank
          - SUM_OF_SCORES_RAW_COL_NAME: column with scores
          - SUM_OF_SCORES_NORMALIZED_COL_NAME: column with normalized scores
          - TRAIT_COL_NAME: column with the trait name
          - SCORE_RAW_COL_NAME: column with the score
          - SCORE_NORMALIZED_COL_NAME: column with the normalized score
          - COMMENTS_COL_NAME: column with the comments
          - COMMENTS_SCORE_RAW_COL_NAME: the normalized score of the commeng
          - COMMENTS_SCORE_NORMALIZED_COL_NAME: the normalized score of the commeng
          - PRIMARY_RANK: whether this is the ranking for the competition

        The scores for the traits are added up based here rather than in the
        spreasheet.  Then, comments are concatenated for that trait.

        The following fields are added:
          - <NAME> Score => { Raw, Normalized }
          - <NAME> Rank => { Raw, Normalized }
          - Then for each unique TRAIT in the TRAIT_COL
            - <NAME> <TRAIT> Judge Data => { Comments => [{ Comment, Judge Id, Score => { Raw, Normalized }]
            - <NAME> <TRAIT> Score => { Raw, Normalized
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
        score_rank_raw_col = header_row.index(score_rank_raw_col_name)
        sum_of_scores_normalized_col = header_row.index(
            sum_of_scores_normalized_col_name
        )
        sum_of_scores_raw_col = header_row.index(sum_of_scores_raw_col_name)
        trait_col = header_row.index(trait_col_name)
        score_normalized_col = header_row.index(score_normalized_col_name)
        score_raw_col = header_row.index(score_raw_col_name)
        comments_col = header_row.index(comments_col_name)
        comments_score_normalized_col = header_row.index(
            comments_score_normalized_col_name
        )
        comments_score_raw_col = header_row.index(comments_score_raw_col_name)
        anonymous_judge_name_col = header_row.index(anonymous_judge_name_col_name) if anonymous_judge_name_col_name else None

        for row in csv_reader:
            application_id = row[app_col]
            if not application_id in self.evaluation_data:
                self.evaluation_data[application_id] = {
                    "%s Score" % self.name: {
                        "Raw": row[sum_of_scores_raw_col],
                        "Normalized": row[sum_of_scores_normalized_col],
                    },
                    "%s Rank" % self.name: {
                        "Raw": row[score_rank_raw_col],
                        "Normalized": row[score_rank_normalized_col],
                    }
                }
                if primary_rank:
                    self.evaluation_data[application_id]["Rank"] = row[
                        score_rank_normalized_col
                    ]

            evaluation_datum = self.evaluation_data[application_id]

            trait_name = row[trait_col].strip()
            if trait_name not in self.traits:
                self.traits.append(trait_name)

            if "%s %s Judge Data" % (self.name, trait_name) not in evaluation_datum:
                evaluation_datum["%s %s Judge Data" % (self.name, trait_name)] = {
                    "Comments": [],
                }
                evaluation_datum["%s %s Score" % (self.name, trait_name)] = {
                    "Raw": 0.0,
                    "Normalized": 0.0,
                }

            evaluation_datum["%s %s Score" % (self.name, trait_name)]["Raw"] = round(
                evaluation_datum["%s %s Score" % (self.name, trait_name)]["Raw"]
                + float(row[score_raw_col]),
                1,
            )
            evaluation_datum["%s %s Score" % (self.name, trait_name)][
                "Normalized"
            ] = round(
                evaluation_datum["%s %s Score" % (self.name, trait_name)]["Normalized"]
                + float(row[score_normalized_col]),
                1,
            )

            comment = {}
            comment["Comment"] = utils.fix_cell(row[comments_col].replace("\n", ""))
            comment["Score"] = {
                "Raw": round(float(row[comments_score_raw_col]), 1),
                "Normalized": round(float(row[comments_score_normalized_col]), 1),
            }
            if anonymous_judge_name_col:
                comment["Anonymous Judge Name"] = row[anonymous_judge_name_col]
            evaluation_datum["%s %s Judge Data" % (self.name, trait_name)]["Comments"].append(comment)

        self.traits.sort()

        self.columns = [
            "%s Score" % self.name,
            "%s Rank" % self.name,
        ]
        self.columns.extend(
            ["%s %s Score" % (self.name, trait) for trait in self.traits]
        )
        self.columns.extend(
            ["%s %s Judge Data" % (self.name, trait) for trait in self.traits]
        )
        if primary_rank:
            self.columns.append("Rank")

    def column_names(self):
        return self.columns

    def cell(self, proposal, column_name):
        if proposal.key() not in self.evaluation_data:
            if column_name == "Rank":
                return "9999"
            if column_name == "%s Score" % self.name:
                return {
                    "Normalized": "N/A",
                    "Raw": "N/A",
                }
            if column_name == "%s Rank" % self.name:
                return {
                    "Normalized": "9999",
                    "Raw ": "9999",
                }
            return {}

        return self.evaluation_data[proposal.key()][column_name]


class ColumnRemover(InformationRemover):
    """Removes a single column from the spreadsheet."""

    def __init__(self, column):
        self.column = column

    def columns_to_remove(self):
        return [self.column]


class ColumnRenamer(InformationTransformer):
    """Renames OLD_COLUMN_NAME to NEW_COLUMN_NAME"""

    def __init__(self, old_column_name, new_column_name):
        self.old_column_name = old_column_name
        self.new_column_name = new_column_name

    def columns_to_remove(self):
        return [self.old_column_name]

    def column_names(self):
        return [self.new_column_name]

    def cell(self, proposal, column_name):
        return proposal.cell(self.old_column_name)


class ColumnCombiner(InformationTransformer):
    """Takes a dictionary of {old_column_name: new_subcolumn_name}
    and a new column name for which to combine these into.  For example
    the dictionary may look like:

    { "Organization State": "State", "Organization Country": "Country" }

    with the new column name of "Organization Location", which would
    create a field "Organization Location" with the value:
    { "State": <value>, "Country": <value> }"""

    def __init__(self, new_column_name, column_config):
        self.new_column_name = new_column_name
        self.column_config = column_config

    def columns_to_remove(self):
        return self.column_config.keys()

    def column_names(self):
        return [self.new_column_name]

    def cell(self, proposal, column_name):
        return {
            new_col: proposal.cell(old_col)
            for (old_col, new_col) in self.column_config.items()
        }


class LocationCombiner(InformationTransformer):
    """Takes Location based columns, and then combines them into a single
    column with the the name"""

    REGION = "Region"
    SUBREGION = "Subregion"
    COUNTRY = "Country"
    STATE = "State/Province"
    LOCALITY = "Locality/District/County"
    ADDRESS_1 = "Street Address"
    ADDRESS_2 = "Address Line 2"
    CITY = "City"
    ZIP_POSTAL = "Zip/Postal Code"
    LAT = "Lat"
    LNG = "Lng"

    import importlib.resources as pkg_resources
    from . import data

    region_data_by_country = {}
    csv_reader = csv.reader(
        pkg_resources.open_text(data, "regionconfig.csv", encoding="utf-8"),
        delimiter=",",
        quotechar='"',
    )
    next(csv_reader)
    for row in csv_reader:
        region_data_by_country[row[0]] = {"subregion": row[1], "region": row[2]}

    country_errors = []

    def __init__(
        self,
        column_name,
        address_1=None,
        address_2=None,
        city=None,
        state=None,
        locality=None,
        country=None,
        zip_postal=None,
        lat=None,
        lng=None,
    ):
        self.column_config = {}
        if country:
            self.column_config[country] = LocationCombiner.COUNTRY
            self.include_region = True
        else:
            self.include_region = False
        if state:
            self.column_config[state] = LocationCombiner.STATE
        if locality:
            self.column_config[locality] = LocationCombiner.LOCALITY
        if address_1:
            self.column_config[address_1] = LocationCombiner.ADDRESS_1
        if address_2:
            self.column_config[address_2] = LocationCombiner.ADDRESS_2
        if city:
            self.column_config[city] = LocationCombiner.CITY
        if zip_postal:
            self.column_config[zip_postal] = LocationCombiner.ZIP_POSTAL
        if lat:
            self.column_config[lat] = LocationCombiner.LAT
        if lng:
            self.column_config[lng] = LocationCombiner.LNG

        self.new_column_name = column_name

    def columns_to_remove(self):
        return self.column_config.keys()

    def column_names(self):
        return [self.new_column_name]

    def cell(self, proposal, column_name):
        data = {
            new_col: proposal.cell(old_col)
            for (old_col, new_col) in self.column_config.items()
        }

        if self.include_region:
            country = data[LocationCombiner.COUNTRY]

            try:
                region = self.region_data_by_country[country]["region"]
                subregion = self.region_data_by_country[country]["subregion"]
                data[LocationCombiner.REGION] = region
                data[LocationCombiner.SUBREGION] = subregion
            except KeyError:
                if country not in self.country_errors:
                    print(
                        "Country %s not in region config file, skipping" % country,
                        file=sys.stderr,
                    )
                    self.country_errors.append(country)
                data[LocationCombiner.REGION] = ""
                data[LocationCombiner.SUBREGION] = ""

        if any(data.values()):
            return data


class PersonCombiner(ColumnCombiner):
    """Takes Location based columns, and then combines them into a single
    column with the the name "<COLUMN_NAME> Location"."""

    FIRST_NAME = "First Name"
    LAST_NAME = "Last Name"
    TITLE = "Title"
    PHONE = "Phone"
    EMAIL = "Email"

    def __init__(
        self,
        column_name,
        first_name=None,
        last_name=None,
        title=None,
        phone=None,
        email=None,
    ):
        new_columns = {}
        if first_name:
            new_columns[first_name] = PersonCombiner.FIRST_NAME
        if last_name:
            new_columns[last_name] = PersonCombiner.LAST_NAME
        if title:
            new_columns[title] = PersonCombiner.TITLE
        if phone:
            new_columns[phone] = PersonCombiner.PHONE
        if email:
            new_columns[email] = PersonCombiner.EMAIL
        super().__init__(column_name, new_columns)


class NameSplitter(InformationTransformer):
    """Takes a column representing a name, and splits on the first space
    into first and last name columns."""

    def __init__(self, column_name, first_name, last_name):
        self.column_name = column_name
        self.first_name = first_name
        self.last_name = last_name

    def columns_to_remove(self):
        return [self.column_name]

    def column_names(self):
        return [self.first_name, self.last_name]

    def cell(self, proposal, column_name):
        if proposal.cell(self.column_name):
            split_name = proposal.cell(self.column_name).split(" ", 1)
            if column_name == self.first_name:
                return split_name[0]
            elif len(split_name) > 1:
                return split_name[1]


class GeocodeProcessor(CellProcessor):
    """Decorates an address column with geocoded lat / lngs."""
    def __init__(self, geocoder):
        self.geocoder = geocoder

    def process_cell(self, proposal, column_name):
        cell = proposal.cell(column_name)
        full_address = Geocoder.Geocoder.get_address_query(
            address1=cell[LocationCombiner.ADDRESS_1],
            address2=cell[LocationCombiner.ADDRESS_2],
            city=cell[LocationCombiner.CITY],
            state=cell[LocationCombiner.STATE],
            country=cell[LocationCombiner.COUNTRY],
            locality=cell[LocationCombiner.LOCALITY],
            zipCode=cell[LocationCombiner.ZIP_POSTAL],
        )
        if full_address == '':
            return ''

        try:
            geocode_result = self.geocoder.geocode(full_address)
            if geocode_result is None:
                print(f"COULD NOT GEOCODE: {full_address}")
            else:
                print(f"GEOCODED: {full_address}")
                cell[LocationCombiner.LAT] = geocode_result.latitude
                cell[LocationCombiner.LNG] = geocode_result.longitude
        except Exception as e:
            print(f"Error Geocoding: {full_address}")
            print(e)

        return cell
