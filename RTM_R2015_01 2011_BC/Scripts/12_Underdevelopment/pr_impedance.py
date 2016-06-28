##---------------------------------------------------------------------
##--TransLink Phase 3 Regional Transportation Model Development
##--
##--Path: translink.emme.?
##--Purpose: Generate Impedance for Park and Ride Access Mode
##---------------------------------------------------------------------
import inro.modeller as _m
import os
import traceback as _traceback

class PrImpedance(_m.Tool()):
    tool_run_msg = _m.Attribute(unicode)

    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Calculate Impedance for Park and Ride Access Mode"
        pb.description = "Calculates Impedance for PnR based on best lot"
        pb.branding_text = "TransLink"

        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)

        return pb.render()

    def run(self):
        with _m.logbook_trace("UNDER DEV - PR Impedance"):
            self.tool_run_msg = ""
            try:
                # TODO: scenario selectors to page and run method
                eb = _m.Modeller().emmebank
                am_scenario = eb.scenario(21000)
                md_scenario = eb.scenario(22000)
                pm_scenario = eb.scenario(23000)
                self(am_scenario, md_scenario, pm_scenario)
                run_msg = "Tool completed"
                self.tool_run_msg = _m.PageBuilder.format_info(run_msg)
            except Exception, e:
                self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc(e))
        pass

    @_m.logbook_trace("UNDER DEV - PNR Impedance")
    def __call__(self, scenarioam, scenariomd, scenariopm):
        util = _m.Modeller().tool("translink.emme.util")

        RailSkim = _m.Modeller().tool("translink.emme.under_dev.wceskim")
        railassign = _m.Modeller().tool("inro.emme.transit_assignment.extended_transit_assignment")
        eb = _m.Modeller().emmebank
        self.matrix_batchins(eb)



    def matrix_batchins(self, eb):
        util = _m.Modeller().tool("translink.emme.util")

        # Lot choice using AM impedances, but lot choice fixed for all time periods
        util.initmat(eb, "mf6000", "buspr-lotChoiceAM", "Bus Best PnR Lot - Bus",0)
        util.initmat(eb, "mf6001", "railpr-lotChoiceAM", "Rail Best PnR Lot - Rail",0)
        util.initmat(eb, "mf6002", "wcepr-lotChoiceAM", "Rail Best PnR Lot -WCE",0)

        # AM Auto generalized Cost same for all modes
        util.initmat(eb, "mf6003", "buspr-gcAutoAM", "PnR Generalized Cost Auto Leg",0)

        # AM bus impedance matrices
        util.initmat(eb, "mf6005", "buspr-GctransitAM", "PnR Generalized Cost Transit Leg - Bus",0)
        util.initmat(eb, "mf6006", "buspr-minGCAM", "PnR Combined Skim Result - Bus",0)
        util.initmat(eb, "mf6007", "buspr-termtimeAM", "PnR Lot Terminal Time - Bus",0)
        util.initmat(eb, "mf6008", "buspr-parkCostAM", "PR parking cost - Bus",0)
        util.initmat(eb, "mf6009", "buspr-auaccessAM", "Auto access time  - Bus",0)
        util.initmat(eb, "mf6010", "buspr-busIVTAM", "Bus IVTT - Bus",0)
        util.initmat(eb, "mf6011", "buspr-busWaitAM", "Bus Wait Time - Bus",0)
        util.initmat(eb, "mf6012", "buspr-boardingsAM", "Boardings - Bus",0)

        # AM rail impedance matrices
        util.initmat(eb, "mf6020", "railpr-GctransitAM", "Rail PnR Generalized Cost Transit Leg - Rail",0)
        util.initmat(eb, "mf6021", "railpr-minGCAM", "Rail PnR Combined Skim Result - Rail",0)
        util.initmat(eb, "mf6022", "railpr-termtimeAM", "PnR Lot Terminal Time - Rail",0)
        util.initmat(eb, "mf6023", "railpr-parkCostAM", "PR parking cost - Rail",0)
        util.initmat(eb, "mf6024", "railpr-auaccessAM", "Auto access time  - Rail",0)
        util.initmat(eb, "mf6025", "railpr-railIVTAM", "Rail IVT - Rail",0)
        util.initmat(eb, "mf6026", "railpr-railWaitAM", "Rail Wait Time - Rail",0)
        util.initmat(eb, "mf6027", "railpr-busIVTAM", "Bus IVT - Rail",0)
        util.initmat(eb, "mf6028", "railpr-busWaitAM", "Bus Wait Time - Rai",0)
        util.initmat(eb, "mf6029", "railpr-boardingsAM", "Rail Boardings",0)

        # AM WCE impedance matrices
        util.initmat(eb, "mf6040", "wcepr-GctransitAM", "WCE PnR Generalized Cost Transit Leg",0)
        util.initmat(eb, "mf6041", "wcepr-minGCAM", "WCE PnR Combined Skim Result",0)
        util.initmat(eb, "mf6042", "wcepr-termtimeAM", "PnR Lot Terminal Time - WCE",0)
        util.initmat(eb, "mf6043", "wcepr-parkCostAM", "PR parking cost - WCE",0)
        util.initmat(eb, "mf6044", "wcepr-auaccessAM", "Auto access time - WCE",0)
        util.initmat(eb, "mf6045", "wcepr-wceIVTAM", "WCE IVT - WCE",0)
        util.initmat(eb, "mf6046", "wcepr-wceWaitAM", "WCE Wait Time - WCE",0)
        util.initmat(eb, "mf6047", "wcepr-railIVTAM", "Rail IVT - WCE",0)
        util.initmat(eb, "mf6048", "wcepr-railWaitAM", "Rail Wait Time - WCE",0)
        util.initmat(eb, "mf6049", "wcepr-busIVTAM", "Bus IVT - WCE",0)
        util.initmat(eb, "mf6050", "wcepr-busWaitAM", "Bus Wait Time - WCE",0)
        util.initmat(eb, "mf6051", "wcepr-boardingsAM", "Boardings - WCE",0)


        # MD Auto generalized Cost same for all modes
        util.initmat(eb, "mf6058", "buspr-gcAutoMD", "PnR Generalized Cost Auto Leg",0)

        # MD bus impedance matrices
        util.initmat(eb, "mf6060", "buspr-GctransitMD", "PnR Generalized Cost Transit Leg - Bus",0)
        util.initmat(eb, "mf6061", "buspr-minGCMD", "PnR Combined Skim Result - Bus",0)
        util.initmat(eb, "mf6062", "buspr-termtimeMD", "PnR Lot Terminal Time - Bus",0)
        util.initmat(eb, "mf6063", "buspr-parkCostMD", "PR parking cost - Bus",0)
        util.initmat(eb, "mf6064", "buspr-auaccessMD", "Auto access time  - Bus",0)
        util.initmat(eb, "mf6065", "buspr-busIVTMD", "Bus IVTT - Bus",0)
        util.initmat(eb, "mf6066", "buspr-busWaitMD", "Bus Wait Time - Bus",0)
        util.initmat(eb, "mf6067", "buspr-boardingsMD", "Boardings - Bus",0)

        # MD rail impedance matrices
        util.initmat(eb, "mf6075", "railpr-GctransitMD", "Rail PnR Generalized Cost Transit Leg - Rail",0)
        util.initmat(eb, "mf6076", "railpr-minGCMD", "Rail PnR Combined Skim Result - Rail",0)
        util.initmat(eb, "mf6077", "railpr-termtimeMD", "PnR Lot Terminal Time - Rail",0)
        util.initmat(eb, "mf6078", "railpr-parkCostMD", "PR parking cost - Rail",0)
        util.initmat(eb, "mf6079", "railpr-auaccessMD", "Auto access time  - Rail",0)
        util.initmat(eb, "mf6080", "railpr-railIVTMD", "Rail IVT - Rail",0)
        util.initmat(eb, "mf6081", "railpr-railWaitMD", "Rail Wait Time - Rail",0)
        util.initmat(eb, "mf6082", "railpr-busIVTMD", "Bus IVT - Rail",0)
        util.initmat(eb, "mf6083", "railpr-busWaitMD", "Bus Wait Time - Rai",0)
        util.initmat(eb, "mf6084", "railpr-boardingsMD", "Rail Boardings",0)

        # MD WCE impedance matrices
        util.initmat(eb, "mf6095", "wcepr-GctransitMD", "WCE PnR Generalized Cost Transit Leg",0)
        util.initmat(eb, "mf6096", "wcepr-minGCMD", "WCE PnR Combined Skim Result",0)
        util.initmat(eb, "mf6097", "wcepr-termtimeMD", "PnR Lot Terminal Time - WCE",0)
        util.initmat(eb, "mf6098", "wcepr-parkCostMD", "PR parking cost - WCE",0)
        util.initmat(eb, "mf6099", "wcepr-auaccessMD", "Auto access time - WCE",0)
        util.initmat(eb, "mf6100", "wcepr-wceIVTMD", "WCE IVT - WCE",0)
        util.initmat(eb, "mf6101", "wcepr-wceWaitMD", "WCE Wait Time - WCE",0)
        util.initmat(eb, "mf6102", "wcepr-railIVTMD", "Rail IVT - WCE",0)
        util.initmat(eb, "mf6103", "wcepr-railWaitMD", "Rail Wait Time - WCE",0)
        util.initmat(eb, "mf6104", "wcepr-busIVTMD", "Bus IVT - WCE",0)
        util.initmat(eb, "mf6105", "wcepr-busWaitMD", "Bus Wait Time - WCE",0)
        util.initmat(eb, "mf6106", "wcepr-boardingsMD", "Boardings - WCE",0)


        # PM Auto generalized Cost same for all modes
        util.initmat(eb, "mf6058", "buspr-gcAutoPM", "PnR Generalized Cost Auto Leg",0)

        # PM bus impedance matrices
        util.initmat(eb, "mf6060", "buspr-GctransitPM", "PnR Generalized Cost Transit Leg - Bus",0)
        util.initmat(eb, "mf6061", "buspr-minGCPM", "PnR Combined Skim Result - Bus",0)
        util.initmat(eb, "mf6062", "buspr-termtimePM", "PnR Lot Terminal Time - Bus",0)
        util.initmat(eb, "mf6063", "buspr-parkCostPM", "PR parking cost - Bus",0)
        util.initmat(eb, "mf6064", "buspr-auaccessPM", "Auto access time  - Bus",0)
        util.initmat(eb, "mf6065", "buspr-busIVTPM", "Bus IVTT - Bus",0)
        util.initmat(eb, "mf6066", "buspr-busWaitPM", "Bus Wait Time - Bus",0)
        util.initmat(eb, "mf6067", "buspr-boardingsPM", "Boardings - Bus",0)

        # PM rail impedance matrices
        util.initmat(eb, "mf6075", "railpr-GctransitPM", "Rail PnR Generalized Cost Transit Leg - Rail",0)
        util.initmat(eb, "mf6076", "railpr-minGCPM", "Rail PnR Combined Skim Result - Rail",0)
        util.initmat(eb, "mf6077", "railpr-termtimePM", "PnR Lot Terminal Time - Rail",0)
        util.initmat(eb, "mf6078", "railpr-parkCostPM", "PR parking cost - Rail",0)
        util.initmat(eb, "mf6079", "railpr-auaccessPM", "Auto access time  - Rail",0)
        util.initmat(eb, "mf6080", "railpr-railIVTPM", "Rail IVT - Rail",0)
        util.initmat(eb, "mf6081", "railpr-railWaitPM", "Rail Wait Time - Rail",0)
        util.initmat(eb, "mf6082", "railpr-busIVTPM", "Bus IVT - Rail",0)
        util.initmat(eb, "mf6083", "railpr-busWaitPM", "Bus Wait Time - Rai",0)
        util.initmat(eb, "mf6084", "railpr-boardingsPM", "Rail Boardings",0)

        # PM WCE impedance matrices
        util.initmat(eb, "mf6095", "wcepr-GctransitPM", "WCE PnR Generalized Cost Transit Leg",0)
        util.initmat(eb, "mf6096", "wcepr-minGCPM", "WCE PnR Combined Skim Result",0)
        util.initmat(eb, "mf6097", "wcepr-termtimePM", "PnR Lot Terminal Time - WCE",0)
        util.initmat(eb, "mf6098", "wcepr-parkCostPM", "PR parking cost - WCE",0)
        util.initmat(eb, "mf6099", "wcepr-auaccessPM", "Auto access time - WCE",0)
        util.initmat(eb, "mf6100", "wcepr-wceIVTPM", "WCE IVT - WCE",0)
        util.initmat(eb, "mf6101", "wcepr-wceWaitPM", "WCE Wait Time - WCE",0)
        util.initmat(eb, "mf6102", "wcepr-railIVTPM", "Rail IVT - WCE",0)
        util.initmat(eb, "mf6103", "wcepr-railWaitPM", "Rail Wait Time - WCE",0)
        util.initmat(eb, "mf6104", "wcepr-busIVTPM", "Bus IVT - WCE",0)
        util.initmat(eb, "mf6105", "wcepr-busWaitPM", "Bus Wait Time - WCE",0)
        util.initmat(eb, "mf6106", "wcepr-boardingsPM", "Boardings - WCE",0)
