##---------------------------------------------------------------------
##--TransLink Phase 2.2 Regional Transportation Model
##--
##--Path: translink.emme.stage5.step10.truckmodel
##--Purpose: Run Full truck Model
##---------------------------------------------------------------------
import inro.modeller as _m
import traceback as _traceback

class FullTruckModel(_m.Tool()):
    Year = _m.Attribute(int)

    tool_run_msg = _m.Attribute(unicode)

    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Full Truck Model Run"
        pb.description = "Run Full Truck Model"
        pb.branding_text = "TransLink"

        pb.add_select(tool_attribute_name="Year",keyvalues=[[2011,"2011"],[2030,"2030"],[2045,"2045"]],
                        title="Choose Analysis Year (2011, 2030 or 2045)")

        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)

        return pb.render()

    def run(self):
        try:
            self.__call__(_m.Modeller().emmebank, self.Year)
            self.tool_run_msg = _m.PageBuilder.format_info("Tool complete")
        except Exception, e:
            self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc(e))

    @_m.logbook_trace("Full Truck Model Run")
    def __call__(self, eb, Year):
        ExternalModel=_m.Modeller().tool("translink.emme.stage5.step10.externaltruck")
        ExternalModel(eb, Year)

        AsiaPacificModel=_m.Modeller().tool("translink.emme.stage5.step10.asiapacifictruck")
        AsiaPacificModel(eb, Year)

        RegionalModel=_m.Modeller().tool("translink.emme.stage5.step10.regionaltruck")
        RegionalModel(eb)

        self.aggregate_demand_pce(eb)

    def aggregate_demand_pce(self, eb):
        util = _m.Modeller().tool("translink.emme.util")

        util.initmat(eb, "mf1040", "CBLgAp", "CB LgTruck AM PCE", 0)
        util.initmat(eb, "mf1041", "CBHvAp", "CB HvTruck AM PCE", 0)
        util.initmat(eb, "mf1042", "IRLgAp", "IR LgTruck AM PCE", 0)
        util.initmat(eb, "mf1043", "IRHvAp", "IR HvTruck AM PCE", 0)
        util.initmat(eb, "mf1044", "APHvAp", "AP HvTruck AM PCE", 0)
        util.initmat(eb, "mf1045", "RGLgAp", "RG LgTruck AM PCE", 0)
        util.initmat(eb, "mf1046", "RGHvAp", "RG HvTruck AM PCE", 0)
        util.initmat(eb, "mf1047", "CBLgMp", "CB LgTruck MD PCE", 0)
        util.initmat(eb, "mf1048", "CBHvMp", "CB HvTruck MD PCE", 0)
        util.initmat(eb, "mf1049", "IRLgMp", "IR LgTruck MD PCE", 0)
        util.initmat(eb, "mf1050", "IRHvMp", "IR HvTruck MD PCE", 0)
        util.initmat(eb, "mf1051", "APHvMp", "AP HvTruck MD PCE", 0)
        util.initmat(eb, "mf1052", "RGLgMp", "RG LgTruck MD PCE", 0)
        util.initmat(eb, "mf1053", "RGHvMp", "RG HvTruck MD PCE", 0)

        specs = []
        # AM LGV
        specs.append(util.matrix_spec("mf1040", "mf1002*1.5"))
        specs.append(util.matrix_spec("mf1042", "mf1012*1.5"))
        specs.append(util.matrix_spec("mf1045", "mf1035*1.5"))
        # AM HGV
        specs.append(util.matrix_spec("mf1041", "mf1005*2.5"))
        specs.append(util.matrix_spec("mf1043", "mf1013*2.5"))
        specs.append(util.matrix_spec("mf1044", "mf1021*2.5"))
        specs.append(util.matrix_spec("mf1046", "mf1037*2.5"))
        # MD LGV
        specs.append(util.matrix_spec("mf1047", "mf1003*1.5"))
        specs.append(util.matrix_spec("mf1049", "mf1014*1.5"))
        specs.append(util.matrix_spec("mf1052", "mf1036*1.5"))
        # MD HGV
        specs.append(util.matrix_spec("mf1048", "mf1006*2.5"))
        specs.append(util.matrix_spec("mf1050", "mf1015*2.5"))
        specs.append(util.matrix_spec("mf1051", "mf1022*2.5"))
        specs.append(util.matrix_spec("mf1053", "mf1038*2.5"))

        # Aggregate total LGV and HGV vehicle demand
        specs.append(util.matrix_spec("mf980", "mf1002 + mf1012 + mf1035"))
        specs.append(util.matrix_spec("mf981", "mf1005 + mf1013 + mf1021 + mf1037"))
        specs.append(util.matrix_spec("mf982", "mf1003 + mf1014 + mf1036"))
        specs.append(util.matrix_spec("mf983", "mf1006 + mf1015 + mf1022 + mf1038"))
        util.compute_matrix(specs)
