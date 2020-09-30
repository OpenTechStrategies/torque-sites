from etl import utils
import csv
import json
import os
import re


class Competition:
    """A Competition of proposals"""

    def __init__(self, proposals_location, name, key_column_name, project_column_name):
        """Initializes the competition form the source spreadsheet in
        PROPOSALS_LOCATION (a file location).  Loads up the CSV and processes
        it.

        NAME refers to the name of the competition, KEY_COLUMN_NAME
        is which column in the base csv holds the identifier for the proposal.
        PROJECT_TITLE_COLUMN_NAME is the title, which is used in generated MediaWiki
        page titles."""
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
        self.columns = next(proposals_reader)
        self.key_column_name = key_column_name
        self.column_types = {}
        self.proposals = {}
        self.sorted_proposal_keys = []
        self.tocs = []
        for row in proposals_reader:
            proposal = Proposal(self.columns, row, key_column_name)
            key = proposal.key()
            self.sorted_proposal_keys.append(key)
            self.proposals[key] = proposal

        self.add_supplemental_information(MediaWikiTitleAdder(project_column_name))

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
        filtered_proposal_keys = [
            p.key()
            for p in self.proposals.values()
            if proposal_filter.proposal_matches(p)
        ]
        self.sorted_proposal_keys = [
            k for k in self.sorted_proposal_keys if k not in filtered_proposal_keys
        ]
        self.proposals = {k: self.proposals[k] for k in self.sorted_proposal_keys}

    def ordered_proposals(self):
        """Returns an array of Proposals ordered by the current sort"""
        return [self.proposals[k] for k in self.sorted_proposal_keys]

    def to_csv(self, output):
        """Writes a csv out to OUTPUT designed to be uploaded to a torque instance"""
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
        initial spradsheet, while ROW is the value for this proposal.
        KEY_COLUMN_NAME is used to later get the key of this proposal.

        This sets up the proposal by processing the initial row"""
        self.data = {}
        self.num_fixed_cells = 0
        self.key_column_name = key_column_name

        for column_name, cell in zip(column_names, row):
            fixed_cell = utils.fix_cell(cell)
            if fixed_cell != cell:
                self.num_fixed_cells += 1
            self.data[column_name] = fixed_cell

    def process_cell_special(self, column_name, processor):
        """Process a cell noted by COLUMN_NAME from PROCESSOR of type CellProcessor"""
        self.data[column_name] = processor.process_cell(self.data[column_name])

    def add_cell(self, column_name, cell):
        """Adds a new value CELL to the place held by COLUMN_NAME"""
        self.data[column_name] = cell

    def cell(self, column_name):
        """Returns the cell value for COLUMN_NAME"""
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
    proposal_matches"""

    def proposal_matches(self, proposal):
        """Return whether the proposal matches this filter.  Should be over
        loaded"""
        return True


class ColumnEqualsProposalFilter(ProposalFilter):
    """A basic filter for when a the value in a given column matches
    the setup value"""

    def __init__(self, column_name, value):
        self.column_name = column_name
        self.value = value

    def proposal_matches(self, proposal):
        return proposal.cell(self.column_name) == self.value


class CellProcessor:
    """The base class for Cell Processors, which implement column_type
    and process_cell"""

    def column_type(self):
        """Return the torque type of the column, or None if using the default
        column type"""
        return None

    def process_cell(self, cell):
        """Transforms the value in CELL to some other value, and returns it"""
        pass


class MultiLineProcessor(CellProcessor):
    """A CellProcessor that splits a cell on comma (',') into a newline
    separate list, for torque to represent as a list"""

    def column_type(self):
        return "list"

    def process_cell(self, cell):
        return "\n".join([elem.strip() for elem in cell.split(",")])


class BudgetTableProcessor(CellProcessor):
    """A CellProcessor specifically for the Budget Table format sent
    from Common Pool, that then gets uploaded as a json document for
    torque to work with."""

    def column_type(self):
        return "json"

    def process_cell(self, cell):
        budget_rows = cell.split("||")
        budget_row_data = []
        for budget_row in budget_rows:
            budget_items = budget_row.split("|")
            budget_amount = NumberCommaizer().process_cell(budget_items[1])
            budget_row_data.append(
                {"description": budget_items[0], "amount": budget_amount}
            )
        return json.dumps(budget_row_data)


class NumberCommaizer(CellProcessor):
    """A CellProcessor that takes large numbers and inserts commas where appropriate,
    and does nothing if it looks like they aren't large numbers."""

    def column_type(self):
        return None

    def process_cell(self, cell):
        """Return the CELL with commas as if it were a large number,
        or do nothing if not parseable as a number"""

        try:
            retn = floor(float(number))
            retn = "{:,}".format(retn)
            return retn
        except Exception as e:
            return cell


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
        import unidecode

        title = "%s (%s)" % (proposal.cell(self.project_column_name), proposal.key())

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

        # Also convert non unicode because we do this with titles on the other side
        return unidecode.unidecode_expect_nonascii(title).strip()


class Attachment:
    """Represents an attachment on the file system, and handles special cases
    about display names to make sure things show up correctly"""

    def __init__(self, key, filename, rank, column_name, path):
        self.file = filename
        self.rank = rank
        self.key = key
        self.path = path
        self.column_name = column_name
        self.name = re.sub("^\\d*_", "", filename)
        self.name = re.sub("\.pdf$", "", self.name)
        if len(self.name) > 33:
            self.name = self.name[0:15] + "..." + self.name[(len(self.name) - 15) :]


class BasicAttachments(InformationAdder):
    """Represents a set of attachments generated from an ATTACHMENT_DIR provided
    at initialization.  These attachments can later be pulled out to upload to
    MediaWiki, but also is an InformationAdder so that those attachments values
    are in the Proposal so that torque knows where they are.

    The column names can be variable based on what attachments are important
    for the competition."""

    defined_column_names = ["Attachment Display Names", "Attachments"]

    def __init__(self, attachments_dir):
        self.attachments = []

        # Attachments are always in a directory structure of
        # <attachments_dir>/<application #>/*
        if attachments_dir is not None and os.path.isdir(attachments_dir):
            for key in os.listdir(attachments_dir):
                if not re.search("^\\d*$", key):
                    continue

                full_application_attachment_dir = os.path.join(attachments_dir, key)
                for attachment_file in os.listdir(full_application_attachment_dir):
                    if re.search("^\\d*_Registration.pdf", attachment_file):
                        continue

                    self.attachments.append(
                        Attachment(
                            key,
                            attachment_file,
                            4,
                            BasicAttachments.defined_column_names[1],
                            os.path.join(
                                full_application_attachment_dir, attachment_file
                            ),
                        )
                    )

    def column_type(self, column_name):
        # List for both, so we don't need to switch on it
        return "list"

    def column_names(self):
        return BasicAttachments.defined_column_names

    def cell(self, proposal, column_name):
        attachments = [a for a in self.attachments if a.key == proposal.key()]

        # Sort first by rank, then by name
        attachments.sort(key=lambda a: str(a.rank) + " " + a.name)

        if column_name == self.defined_column_names[0]:
            return "\n".join([a.name for a in attachments])
        elif column_name == self.defined_column_names[1]:
            return "\n".join([a.file for a in attachments])
        else:
            raise Exception(column_name + "is not a valid attachment column name")
