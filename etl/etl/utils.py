import re
import warnings
from bs4 import BeautifulSoup

# Used in converting "<foo>&nbsp;<bar>" and "</foo>&nbsp;<bar>"
# to "<foo> <bar>" and "</foo> <bar>" respectively.  (Those particular
# instances of "&nbsp;" in the data are not very convincing, and they
# create noise when we're looking for unnecessary escaping elsewhere.)
intertag_nbsp_re = re.compile("(?m)(</?[a-z]+>)&nbsp;(<[a-z]+>)")

# Matches Unicode 8226 (U+2022) at the beginning of a line,
# which is something that applicants do in a lot of fields.
bullets_re = re.compile("^•", re.MULTILINE)


def commize_number(number):
    try:
        retn = floor(float(number))
        retn = "{:,}".format(retn)
        return retn
    except Exception as e:
        return number


def collapse_replace(string, old, new):
    "Return STRING, with OLD repeatedly replaced by NEW until no more OLD."
    while string.find(old) != -1:
        string = string.replace(old, new)
    return string


def weaken_the_strong(html):
    """Strip any meaningless <strong>...</strong> tags from HTML.
    HTML is a Unicode string; the return value is either HTML or a new
    Unicode string based on HTML.

    If <strong> tags cover everything in HTML, remove the tags.  But if
    <strong> tags are used only sometimes, maybe they're meaningful, so
    leave them.  Basically, we want to make strength great again."""
    # If there's no strength here, move on.
    if not "<strong>" in html:
        return html

    # Remove the stuff inside strong tags
    soup = BeautifulSoup(html, "html.parser")
    while "<strong>" in str(soup):
        soup.strong.extract()

    # Check whether the non-bold stuff is more than just tags and
    # punctuation.  If not, all the important stuff was bold, so strip
    # bold and return.
    if re.sub(r"\W", "", soup.get_text()) == "":
        return re.sub("</?strong>", "", html)

    # OTOH, if the non-bold stuff contained letters or numbers, maybe
    # there's real content there, which means the html was a mix of
    # bold and non-bold text.  Better to leave it alone.
    return html


def form_well(html):
    """Return a well-formed version of HTML with dangling tags closed.
    Some of the input includes tables that cut off without closing
    tags; some entries leave <td> tags open too."""
    # Parse html and suppress warnings about urls in the text
    warnings.filterwarnings("ignore", category=UserWarning, module="bs4")
    soup = BeautifulSoup(html, "html.parser")

    # Return well-formed html as a soup object
    return soup


def fix_cell(cell):
    """Return a cleaned up version of the CELL that will work well
    with mediawiki, mainly through text subsitution."""
    # A straight-up HTML-unescaping might be the right thing
    # (i.e., cell = html_parser.unescape(cell) below)
    # in the long run, but for now, let's do the same limited
    # set of unescapings the original 'sanitize' script did:
    cell = cell.replace("&amp;", "&")
    cell = cell.replace("&lt;", "<")
    cell = cell.replace("&gt;", ">")
    # The rest should be recursively collapsing replacements:
    cell = collapse_replace(cell, "\t", " ")
    cell = collapse_replace(cell, "&nbsp;&nbsp;", "&nbsp;")
    cell = collapse_replace(cell, "&nbsp; ", " ")
    cell = collapse_replace(cell, " &nbsp;", " ")
    cell = collapse_replace(cell, "&nbsp;</", "</")
    cell = collapse_replace(cell, '\\"', '"')
    cell = cell.replace("\n", "<br/>\n")
    cell = re.sub(intertag_nbsp_re, "\\1 \\2", cell)

    soup = form_well(cell)
    cell = weaken_the_strong(str(soup))

    # The parsing for lists requires an asterisk at the start
    # of the line, but some entries use bullets. This regex
    # swaps the bullets for asterisks.
    cell = bullets_re.sub("*", cell)

    # We don't want to have extra new lines added at the beginning or end
    # because that could make the wiki formatting odd
    cell = cell.strip()

    if cell.lower() == "null":
        cell = ""

    if cell.lower() == "not applicable":
        cell = ""

    return cell


def commaize_number(number):
    """Return the NUMBER with commas as if it were a large number,
    or do nothing if not parseable as a number"""

    try:
        retn = floor(float(number))
        retn = "{:,}".format(retn)
        return retn
    except Exception as e:
        return number


def parse_pare(pare_option):
    """Parses the PARE_OPTION and returns a tuple of
    (PARE_FACTOR, KEYS_TO_INCLUDE) where PARE_FACTOR is an int
    by which proposals should be reduced, and KEYS_TO_INCLUDE
    is a list of proposals to include by key.  Exactly one of the
    two will be a value, with the other being None."""

    pare_factor = None
    keys_to_include = None
    if pare_option is None:
        pass
    elif pare_option.startswith("@"):
        with open(pare_option[1:]) as pare_file:
            keys_to_include = [
                l.strip().split(" ")[0] for l in pare_file.readlines() if l.strip()
            ]
    elif pare_option.startswith("+"):
        keys_to_include = pare_option[1:].split(",")
    else:
        try:
            pare_factor = int(pare_option)
        except:
            raise Exception("Pare option not a number: " + pare_option)
    return (pare_factor, keys_to_include)
