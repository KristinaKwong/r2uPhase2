##---------------------------------------------------------------------
##--TransLink Phase 2.2 Regional Transportation Model
##--
##--Path: translink.emme.stage1.step0.settings
##--Purpose: sets model values
##---------------------------------------------------------------------
import inro.modeller as _m
import traceback as _traceback
import csv
import os


class InputSettings(_m.Tool()):
    file_name = _m.Attribute(unicode)
    tool_run_msg = ""

    def page(self):
        pb = _m.ToolPageBuilder(self)
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

        emmebank_dir = os.path.dirname(_m.Modeller().emmebank.path)

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
            eb = _m.Modeller().emmebank
            self(eb, self.file_name)
            self.tool_run_msg = _m.PageBuilder.format_info("Tool complete")
        except Exception, error:
            self.tool_run_msg = _m.PageBuilder.format_exception(
                error, _traceback.format_exc(error))
            raise

    @_m.logbook_trace("Read settings from settings.csv", save_arguments=True)
    def __call__(self, eb, file_name):
        util = _m.Modeller().tool("translink.emme.util")

        ## Read the settings file
        util.initmat(eb, "ms138", "ConTrn", "Run Congested Transit Assignment", 0)
        util.initmat(eb, "ms139", "PnRMod", "Run Park and Ride Model", 0)
        util.initmat(eb, "ms140", "AMScNo", "AM Scenario Number", 0)
        util.initmat(eb, "ms141", "MDScNo", "MD Scenario Number", 0)
        util.initmat(eb, "ms142", "ProNum", "Number of Processors", 0)
        util.initmat(eb, "ms143", "ScCrMo", "Scenario Creation Module", 0)
        util.initmat(eb, "ms144", "PrCal", "Parking Cost Adjustment", 0)
        util.initmat(eb, "ms145", "DisSen", "Trip Dist Cost Sens", 0)
        util.initmat(eb, "ms146", "MChSen", "Mode Choice Toll Sens", 0)
        util.initmat(eb, "ms147", "AsgSen", "Assignment Toll Sens", 0)
        util.initmat(eb, "ms148", "DsToSn", "Trip Dist Cost (Toll) Sens", 0)
        util.initmat(eb, "ms149", "year", "Model Horizon Year", 0)

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
                      'congested_transit': 'ms138',
                      'park_and_ride': 'ms139',
                      'model_year': 'ms149'}

        truth_values = {"on": 1, "off": 0}
        # prepare report to logbook
        pb = _m.PageBuilder(title="Input settings")
        text = []

        # Read data from file
        # Header should be Label, Setting, Value
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
                    scalar = eb.matrix(matrix)
                    if scalar:
                        scalar.data = value
                    text.append("   %(Setting)-45s: %(Value)-15s (%(Label)s)" % line)
                elif line["Label"]:
                    raise Exception("Unknown parameter %s found in settings file" % line["Label"])

        pb.add_html("<div class=\"preformat\"\>%s</div>" % "\n".join(text))
        _m.logbook_write(name="Settings report", value=pb.render())
