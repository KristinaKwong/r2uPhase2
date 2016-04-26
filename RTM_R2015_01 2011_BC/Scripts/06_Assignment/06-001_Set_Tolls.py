##---------------------------------------------------------------------
##--TransLink Phase 2.2 Regional Transportation Model
##--
##--Path: translink.emme.stage3.step6.tollset
##--Purpose: initialize @tolls and read in values from external file
##---------------------------------------------------------------------
import inro.modeller as _m
import traceback as _traceback
import os

class SetTolls(_m.Tool()):
    root_directory = os.path.dirname(_m.Modeller().emmebank.path)
    toll_file = root_directory + "tollinput.csv"
    tool_run_msg = ""

    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Toll Input Module"
        pb.description = "Add toll values to extra attribute"
        pb.branding_text = "TransLink"

        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)

        return pb.render()


    def run(self):
        self.tool_run_msg = ""
        try:
            # TODO: add toll_file and scenario selectors to page and run method
            self(self.toll_file)
            self.tool_run_msg = _m.PageBuilder.format_info("Tool complete")
        except Exception, error:
            self.tool_run_msg = _m.PageBuilder.format_exception(
                error, _traceback.format_exc(error))
            raise

    @_m.logbook_trace("Setting toll values", save_arguments=True)
    def __call__(self, toll_file, scenarioam, scenariomd, scenariopm):
        network_calc = _m.Modeller().tool("inro.emme.network_calculation.network_calculator")
        with _m.logbook_trace("Read new tolls in from file"):
            # TODO: see if this can be replaced by input attribute values tool
            with open(toll_file, "r") as f:
                #read toll csv file and check number of toll links to set
                getlines = f.readlines()
                tollsize = len(getlines)
                f.close()
            with _m.logbook_trace("Assigning tolls with network calculator"):
                #Note index starts with 1, this assumes the header line is skipped
                spec = {
                    "result": "@tolls",
                    "expression": "0",
                    "aggregation": None,
                    "selections": {
                        "link": "all"
                    },
                    "type": "NETWORK_CALCULATION"
                }
                network_calc(spec, scenario=scenarioam)
                network_calc(spec, scenario=scenariomd)
                network_calc(spec, scenario=scenariopm)

                for x in xrange(1, tollsize):
                    activeline = getlines[x]
                    bridgename, inode, jnode, temptoll = activeline.split(",")
                    tollvalue = temptoll.rstrip()   #remove the EOL character from each toll

                    spec["expression"] = str(tollvalue)
                    spec["selections"]["link"] = "i=" + str(inode) + " and j=" + str(jnode)

                    network_calc(spec, scenario=scenarioam)
                    network_calc(spec, scenario=scenariomd)
                    network_calc(spec, scenario=scenariopm)
