from etl import field_allowlist

import requests
import pprint
import json
import csv


class Submittable:
    """Main entry point for interacting with submittable API

    The primary way to use it is to initialize it, and then call
    one of:

        get_submissions_as_torque - Gets an array of objects matching to 
        as you would use in the rest of the ETL pipeline

        output_data_file - outputs the submissions to a data file that
        can be imported by competition.JsonBasedCompetition

        output_column_spreadsheet - for debugging use, creates a spreadsheet
        that has the current column information."""

    UNKNOWN = "UNKNOWN"

    allowed_torque_fields = [item for sublist in field_allowlist.allowlist.values() for item in sublist]
    allowed_torque_fields.append(UNKNOWN)


    def __init__(self, api_key, torque_mappings, registration_project, application_project):
        """Requires API_KEY, which is the one to access the submittable api,
        as well as TORQUE_MAPPINGS, a dictionary that maps from submittable
        field IDs to torque columns from the allowlist.

        Those mappings can include a | character, which denotes that only
        the part of the name before the | should be matched against the allowlist.

        If False, that field will be skipped on conversion, and if set to
        Submittable.UNKNOWN, it will also be skipped, which is useful when
        mapping things out.

        REGISTRATION_PROJECT is the project for the registrations, and the
        APPLICATION project is the one for the applications.  This may change
        in the future and need to be refactored if future competitions do it
        differently."""
        self.api_key = api_key
        self.torque_mappings = torque_mappings
        self.registration_project = registration_project
        self.application_project = application_project
        self.pp = pprint.PrettyPrinter(indent=2)
        self.forms = {}

    def get_from_submittable(self, path, params={}):
        uri = "https://submittable-api.submittable.com/v3/" + path
        r = requests.get(uri, auth=requests.auth.HTTPBasicAuth(self.api_key, ""), params=params)
        return r.json()
    
    def get_form_ids(self):
        return list(set([item['formId'] for item in self.get_from_submittable("forms")['items']]))
    
    def get_fields(self, form_id):
        return self.get_from_submittable("forms/%s" % form_id)["fields"]
    
    def dump_forms(self):
        """Useful for debugging the fields, to get all the information available"""

        for form_id in self.get_form_ids():
            fields = self.get_fields(form_id)
            print('-------------------------------')
            print('FORM ID: ' + form_id)
            print('--------')
            for field in fields:
                print(field['formFieldId'] + ": " + field.get('label', ''))

    def get_form(self, form_id):
        if form_id not in self.forms:
            self.forms[form_id] = self.get_from_submittable("forms/%s" % form_id)
    
        form = self.forms[form_id]
        form['field_dict'] = {}
        for field in form['fields']:
            form['field_dict'][field['formFieldId']] = field
    
        return form
    
    # All the long form stuff comes in a special draft.js format.  See:
    #   https://developers.aprimo.com/digital-asset-management/working-with-rich-content-fields-article-editor/
    def convert_draft_js_to_text(self, draft_js):
        resp = ""
        for block in draft_js["blocks"]:
            if block['depth'] != 0:
                raise Exception("Depth of non zero, need to figure out")
    
            if block["type"] == "unstyled":
                resp += block["text"]
            elif block["type"] == "unordered-list-item":
                resp += "* " + block["text"]
            elif block["type"] == "header-one":
                resp += "== " + block["text"] + " =="
            elif block["type"] == "header-two":
                resp += "=== " + block["text"] + " ==="
            elif block["type"] == "code-block":
                resp += block["text"]
            else:
                self.pp.pprint(draft_js)
                raise Exception("Can't handle block type %s" % block["type"])
    
            resp += "\n"
    
        return resp
    
    def get_full_submission(self, submission):
        def convert_field_response_to_torque(field, field_response):
            if field['fieldType'] in ['title', 'short_answer', 'phone', 'email', 'website']:
                return field_response['value'].strip()
            elif field['fieldType'] == 'number':
                return field_response['value']
            elif field['fieldType'] in ['dropdown_list', 'single_response']:
                if len(field_response['options']) == 0:
                    return ""
    
                if len(field_response['options']) != 1:
                    raise Exception("Option list has not exactly one option, which shouldn't be possible")
    
                for option in field['options']:
                    if option['formOptionId'] == field_response['options'][0]:
                        return option['label'].strip()
                if not found:
                    raise Exception("Option wasn't found, which is weird")
    
            elif field['fieldType'] in ['multiple_response']:
                response = []
                for response_option in field_response['options']:
                    found = False
                    for option in field['options']:
                        if option['formOptionId'] == response_option:
                            response.append(option['label'].strip())
                            found = True
    
                    if not found:
                        raise Exception("Option wasn't found, which is weird")
    
                return response
            elif field['fieldType'] == 'name':
                return {
                    'first_name': field_response['firstName'].strip(),
                    'last_name': field_response['lastName'].strip(),
                }
            elif field['fieldType'] == 'eligibility_single_checkbox':
                return str(field_response['value'].strip())
            elif field['fieldType'] == 'long_answer':
                return self.convert_draft_js_to_text(json.loads(field_response['value'].strip()))
            else:
                print("Can't convert fieldtype %s" % field['fieldType'])
                print("Field was:")
                self.pp.pprint(field)
                print("Response was:")
                self.pp.pprint(field_response)
                raise Exception("Failed to convert field")
    
        submission = self.get_from_submittable("submissions/%s" % submission['submissionId'])
        submission['torque_fields'] = {}
        for form_response in submission['formResponses']:
            form = self.get_form(form_response['formId'])
    
            for field_response in form_response['fieldData']:
                field = form['field_dict'][field_response['formFieldId']]
                torque_label = self.torque_mappings.get(field['formFieldId'], None)
                if torque_label == None:
                    print("Warning: %s is not in torque mapping.  Submittable label is %s" % (field['formFieldId'], field['label']))
    
                if torque_label and torque_label.split("|")[0] not in Submittable.allowed_torque_fields:
                    print("Warning: %s is not a valid torque mapping.  Submittable label was %s" % (torque_label, field['formFieldId']))
    
                if torque_label:
                    submission['torque_fields'][field['formFieldId']] = {
                        "label": field['label'],
                        "torque_label": torque_label,
                        "value": convert_field_response_to_torque(field, field_response),
                    }
    
        return submission

    def get_submissions(self, project=None):
        payload = {"pageSize": 100}
        if project:
            payload['Projects.Include'] = [project]
        page = self.get_from_submittable("submissions", payload)
        items = page["items"]
    
        for page_number in range(1, page["totalPages"]):
            payload['page'] = page_number + 1
            page = self.get_from_submittable("submissions", payload)
            items.extend(page["items"])

        return items
    
    def get_submissions_as_torque(self):
        """Returns the submissions with their corresponding torque fields.
        There's also extra information such as the original label, the original
        field id."""
        
        registration_submissions = self.get_submissions(self.registration_project)
        application_submissions = self.get_submissions(self.application_project)
    
        torque_submissions = []

        for application_sub in application_submissions:
            torque_fields = {}
            found = False
            for registration_sub in registration_submissions:
                if registration_sub['submitterId'] == application_sub['submitterId']:
                    torque_fields.update(self.get_full_submission(registration_sub)['torque_fields'])
                    found=True
    
            torque_fields.update(self.get_full_submission(application_sub)['torque_fields'])
    
            if not found:
                raise Exception("Weird that there's an Application submissions without a registration")
            torque_submissions.append(torque_fields)
    
        return torque_submissions
    
    def output_data_file(self, filename):
        """Output a json file to FILENAME that can be imported by
        competition.JsonBasedCompetition"""
        torque_data = []
        for sub in self.get_submissions_as_torque():
            datum = {}
            for (submittable, torque) in self.torque_mappings.items():
                if submittable in sub:
                    datum[torque] = sub[submittable]["value"]
                elif torque:
                    datum[torque] = ""
            torque_data.append(datum)
    
        json.dump(torque_data, open(filename, "w"))
    
    def output_column_spreadsheet(self, filename):
        """Output a spreadsheet to FILENAME with the columns:

          * Field ID
          * Field Label
          * Allowlist field name
          * Sample Data

        which is useful for figuring out what allowlist mappings should
        apply to which field ids."""
        subs = self.get_submissions_as_torque()
    
        csv_writer = csv.writer(open(filename, "w"), delimiter=",", quotechar='"', lineterminator="\n")
    
        csv_writer.writerow([
            "Field ID",
            "Field Label",
            "Allowlist field name",
            "Sample Data",
        ])
    
        seen_field_ids = []
        for sub in subs:
            for (field_id, data) in sub.items():
                if field_id not in seen_field_ids:
                    seen_field_ids.append(field_id)
                    csv_writer.writerow([
                        field_id,
                        data['label'],
                        data['torque_label'],
                        data['value'],
                    ])
