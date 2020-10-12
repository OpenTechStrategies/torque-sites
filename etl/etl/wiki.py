import mwclient
import json
import io
from etl import competition


class WikiSession:
    """Represents a session that's logged into a wiki to upload all
    of the information about a competition.  Requires a user, password
    competition name, and a url.  These are usually configured in the
    etl pipelines in a config.py"""

    def __init__(self, username, password, competition_name, url):
        (scheme, host) = url.split("://")

        # We need a very large timeout because uploading reindexes everything!
        self.site = mwclient.Site(host, path="/", scheme=scheme, reqs={"timeout": 300})
        self.site.login(username, password)
        self.competition_name = competition_name

    def upload_sheet(self, comp):
        """Uploads the sheet, the tocs, and creates the pages for
        a Competition COMP"""
        self.site.raw_call(
            "api",
            {
                "action": "torquedataconnectuploadsheet",
                "format": "json",
                "object_name": "proposal",
                "sheet_name": self.competition_name,
                "key_column": comp.key_column_name,
            },
            {"data_file": comp.to_csv(io.StringIO()).getvalue()},
        )

        for toc in comp.tocs:
            self.upload_toc(toc)

        self.create_pages(comp)

    def upload_attachments(self, attachments):
        """Uploads all the ATTACHMENTS, which is a list of
        competition.Attachment"""
        for attachment in attachments:
            print("Uploading " + attachment.file)
            with open(attachment.path, "rb") as attachment_stream:
                self.site.raw_call(
                    "api",
                    {
                        "action": "torquedataconnectuploadattachment",
                        "format": "json",
                        "sheet_name": self.competition_name,
                        "object_id": attachment.key,
                        "permissions_column": attachment.column_name,
                        "attachment_name": attachment.file,
                    },
                    {"attachment": attachment_stream.read()},
                )

    def upload_toc(self, toc):
        """Upload a Toc represented by TOC, which will also create the page
        for the Toc if it doesn't already exist on the wiki"""
        self.site.raw_call(
            "api",
            {
                "action": "torquedataconnectuploadtoc",
                "format": "json",
                "sheet_name": self.competition_name,
                "toc_name": toc.name,
            },
            {"template": toc.template_file(), "json": json.dumps(toc.grouped_data())},
        )

        p = self.site.pages[toc.name]
        if not p.exists:
            p.save(
                "{{ #tdcrender:%s/toc/%s.mwiki }}" % (self.competition_name, toc.name)
            )

    def create_pages(self, comp):
        """Creates all the pages in the Competition COMP according to their
        wiki title, which will only upload if the page doesn't already exist.

        That page will have a single line contaning the #tdcrender call."""
        for proposal in comp.ordered_proposals():
            page_title = proposal.cell(
                competition.MediaWikiTitleAdder.title_column_name
            )

            if page_title is None:
                raise Exception("Competition needs the page title adder run")

            self.create_page(
                page_title,
                "{{ #tdcrender:%s/id/%s.mwiki }}"
                % (self.competition_name, proposal.key()),
            )

    def create_page(self, page_title, body, create_if_exists=False):
        if not page_title:
            return

        p = self.site.pages[page_title]
        if not p.exists or create_if_exists:
            p.save(body)
