##--------------------------------------------------
##--TransLink Phase 2 Regional Transportation Model
##--00_02_settings.py
##--Path: translink.emme.settings
##--Purpose: sets model values
##--------------------------------------------------
##--Last modified 2015-02-12 Kevin Bragg (INRO)
##--Reason: Added check for missing values and raise
##--Last modified 2015-01-21 Kevin Bragg (INRO)
##--Reason: Add reference for congested transit
##          assignment and park and ride in settings
##--Last modified 2014-02-14 Kevin Bragg (INRO)
##--Reason: Update to Emme 4.0 namespaces
##          Code cleanup PEP 8 compliance
##          Changed format of settings.csv file
##          Added page description, logging of settings report
##--Last modified 2013-11-01 Rhys Wolff (HDR)
##--Last modification reason - development
##---------------------------------------------------
##--Called by: Model run procedure
##--Calls:     None
##--Accesses:  settings.csv
##--Outputs: None
##---------------------------------------------------
##--Status/additional notes:
##--Supersedes all earlier versions of settings.py
##---------------------------------------------------

import inro.modeller as _m
import traceback as _traceback
import csv
import os


class InputSettings(_m.Tool()):
    file_name = _m.Attribute(unicode)
    tool_run_msg = ""

    def page(self):
        emmebank_dir = os.path.dirname(_m.Modeller().emmebank.path)

        pb = _m.ToolPageBuilder(self, title="Land Use Input Module")
        pb.title = "Define model run settings"
        pb.description = """
<div align="left">
Import the settings from the specified file input.
Note that the settings file must contain as a first line the header:
<br>
<div class=\"preformat\"\>
    Label, Description, Value
</div>
<br><br>
And the following parameter names must be used under Label:
<br>
<div class=\"preformat\"\>
    am_scenario, md_scenario, num_processors, create_scenarios,
    park_cost_adjust, cost_sens, mode_choice_sens, toll_assign_sens,
    toll_dist_sens, congested_transit, park_and_ride
</div>
<br><br>
Whitespace is ignored.
</div>"""
        pb.branding_text = "TransLink"

        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)

        pb.add_select_file(tool_attribute_name="file_name",
                           window_type="file",
                           file_filter='*.csv',
                           start_path=emmebank_dir,
                           title="Select settings.csv file: ",
                           note="File must be csv file.")

        return pb.render()

    def run(self):
        self.tool_run_msg = ""
        try:
            self(self.file_name)
            self.tool_run_msg = _m.PageBuilder.format_info("Tool complete")
        except Exception, error:
            self.tool_run_msg = _m.PageBuilder.format_exception(
                error, _traceback.format_exc(error))
            raise

    @_m.logbook_trace("Read settings from settings.csv", save_arguments=True)
    def __call__(self, file_name):
        eb = _m.Modeller().emmebank
        # Scalars to hold corresponding settings
        input_mats = {'am_scenario': 'ms140',
                      'md_scenario': 'ms141',
                      'num_processors': 'ms142',
                      'create_scenarios': 'ms143',
                      'park_cost_adjust': 'ms144',
                      'cost_sens': 'ms145',
                      'mode_choice_sens': 'ms146',
                      'toll_assign_sens': 'ms147',
                      'toll_dist_sens': 'ms148',
                      'congested_transit': 'not_a_matrix',
                      'park_and_ride': 'not_a_matrix'}
        # TODO: these scalars could be created (overwritten) from this script
        # NOTE: the setting implementation uses a mixture of old-style
        #       EMME/2 convention of saving settings as booleans in
        #       scalar matrices and new style use of Python dictionary
        truth_values = {"on": 1, "off": 0}
        # prepare report to logbook
        pb = _m.PageBuilder(title="Input settings")
        text = []

        # Read data from file
        # Header should be Label, Setting, Value
        result = {}
        with open(file_name, 'r') as settings_file:
            reader = csv.DictReader(settings_file, skipinitialspace=True)
            for line in reader:
                matrix = input_mats[line["Label"]]
                if matrix:
                    value = line["Value"]
                    if not value:
                        raise Exception("Missing value for parameter %s in settings file" % line["Label"])
                    value = value.lower()
                    value = float(truth_values.get(value, value))
                    result[line["Label"]] = value
                    scalar = eb.matrix(matrix)
                    if scalar:
                        scalar.data = value
                    text.append("   %(Setting)-45s: %(Value)-15s (%(Label)s)" % line)
                elif line["Label"]:
                    raise Exception("Unknown parameter %s found in settings file" % line["Label"])

        pb.add_html("<div class=\"preformat\"\>%s</div>" % "\n".join(text))
        _m.logbook_write(name="Settings report", value=pb.render())
        return result
