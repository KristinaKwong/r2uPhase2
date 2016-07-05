##---------------------------------------------------------------------
##--TransLink Phase 3 Regional Transportation Model Development
##--
##--Path: translink.emme.?
##--Purpose: Generate Impedance for Park and Ride Access Mode
##---------------------------------------------------------------------
import inro.modeller as _m
import os
import csv
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
        eb = _m.Modeller().emmebank
        util = _m.Modeller().tool("translink.emme.util")
        input_path = util.get_input_path(eb)
        pnr_costs = os.path.join(input_path, "pnr_inputs.csv")

        RailSkim = _m.Modeller().tool("translink.emme.under_dev.wceskim")
        railassign = _m.Modeller().tool("inro.emme.transit_assignment.extended_transit_assignment")

        self.matrix_batchins(eb)
        self.read_file(eb, pnr_costs)




    @_m.logbook_trace("UNDER DEV - PNR Impedance")
    def matrix_batchins(self, eb):
        util = _m.Modeller().tool("translink.emme.util")

        #TODO move the VOT to actual file Batchin -

        # Lot choice using AM impedances, but lot choice fixed for all time periods
        util.initmat(eb, "mf6000", "buspr-lotChceWkAM", "Bus Best PnR Lot - Bus",0)
        util.initmat(eb, "mf6001", "railpr-lotChceWkAM", "Rail Best PnR Lot - Rail",0)
        util.initmat(eb, "mf6002", "wcepr-lotChceWkAM", "Rail Best PnR Lot -WCE",0)


        # AM Auto generalized Cost same for all modes
        util.initmat(eb, "mf6003", "buspr-gcAutoAM", "PnR Generalized Cost Auto Leg",0)


        # AM bus impedance matrices
        util.initmat(eb, "mf6005", "buspr-GctranWkAM", "PnR Generalized Cost Transit Leg - Bus",0)
        util.initmat(eb, "mf6006", "buspr-minGCWkAM", "PnR Combined Skim Result - Bus",0)
        util.initmat(eb, "mf6007", "buspr-trmtimWkAM", "PnR Lot Terminal Time - Bus",0)
        util.initmat(eb, "mf6008", "buspr-prkostWkAM", "PR parking cost - Bus",0)
        util.initmat(eb, "mf6009", "buspr-autAcsWkAM", "Auto access time  - Bus",0)
        util.initmat(eb, "mf6010", "buspr-busIVTWkAM", "Bus IVTT - Bus",0)
        util.initmat(eb, "mf6011", "buspr-busWtWkAM", "Bus Wait Time - Bus",0)
        util.initmat(eb, "mf6012", "buspr-bordsWkAM", "Boardings - Bus",0)


        # AM rail impedance matrices
        util.initmat(eb, "mf6020", "railpr-GctranWkAM", "Rail PnR Generalized Cost Transit Leg - Rail",0)
        util.initmat(eb, "mf6021", "railpr-minGCWkAM", "Rail PnR Combined Skim Result - Rail",0)
        util.initmat(eb, "mf6022", "railpr-trmtimWkAM", "PnR Lot Terminal Time - Rail",0)
        util.initmat(eb, "mf6023", "railpr-prkostWkAM", "PR parking cost - Rail",0)
        util.initmat(eb, "mf6024", "railpr-autAcsWkAM", "Auto access time  - Rail",0)
        util.initmat(eb, "mf6025", "railpr-railIVTWkAM", "Rail IVT - Rail",0)
        util.initmat(eb, "mf6026", "railpr-railWtWkAM", "Rail Wait Time - Rail",0)
        util.initmat(eb, "mf6027", "railpr-busIVTWkAM", "Bus IVT - Rail",0)
        util.initmat(eb, "mf6028", "railpr-busWtWkAM", "Bus Wait Time - Rai",0)
        util.initmat(eb, "mf6029", "railpr-bordsWkAM", "Rail Boardings",0)


        # AM WCE impedance matrices
        util.initmat(eb, "mf6040", "wcepr-GctranWkAM", "WCE PnR Generalized Cost Transit Leg",0)
        util.initmat(eb, "mf6041", "wcepr-minGCWkAM", "WCE PnR Combined Skim Result",0)
        util.initmat(eb, "mf6042", "wcepr-trmtimWkAM", "PnR Lot Terminal Time - WCE",0)
        util.initmat(eb, "mf6043", "wcepr-prkostWkAM", "PR parking cost - WCE",0)
        util.initmat(eb, "mf6044", "wcepr-autAcsWkAM", "Auto access time - WCE",0)
        util.initmat(eb, "mf6045", "wcepr-wceIVTWkAM", "WCE IVT - WCE",0)
        util.initmat(eb, "mf6046", "wcepr-wceWtWkAM", "WCE Wait Time - WCE",0)
        util.initmat(eb, "mf6047", "wcepr-railIVTWkAM", "Rail IVT - WCE",0)
        util.initmat(eb, "mf6048", "wcepr-railWtWkAM", "Rail Wait Time - WCE",0)
        util.initmat(eb, "mf6049", "wcepr-busIVTWkAM", "Bus IVT - WCE",0)
        util.initmat(eb, "mf6050", "wcepr-busWtWkAM", "Bus Wait Time - WCE",0)
        util.initmat(eb, "mf6051", "wcepr-bordsWkAM", "Boardings - WCE",0)


        # MD Auto generalized Cost same for all modes
        util.initmat(eb, "mf6058", "buspr-gcAutoWkMD", "PnR Generalized Cost Auto Leg",0)


        # MD bus impedance matrices
        util.initmat(eb, "mf6060", "buspr-GctranWkMD", "PnR Generalized Cost Transit Leg - Bus",0)
        util.initmat(eb, "mf6061", "buspr-minGCWkMD", "PnR Combined Skim Result - Bus",0)
        util.initmat(eb, "mf6062", "buspr-trmtimWkMD", "PnR Lot Terminal Time - Bus",0)
        util.initmat(eb, "mf6063", "buspr-prkostWkMD", "PR parking cost - Bus",0)
        util.initmat(eb, "mf6064", "buspr-autAcsWkMD", "Auto access time  - Bus",0)
        util.initmat(eb, "mf6065", "buspr-busIVTWkMD", "Bus IVTT - Bus",0)
        util.initmat(eb, "mf6066", "buspr-busWtWkMD", "Bus Wait Time - Bus",0)
        util.initmat(eb, "mf6067", "buspr-bordsWkMD", "Boardings - Bus",0)


        # MD rail impedance matrices
        util.initmat(eb, "mf6075", "railpr-GctranWkMD", "Rail PnR Generalized Cost Transit Leg - Rail",0)
        util.initmat(eb, "mf6076", "railpr-minGCWkMD", "Rail PnR Combined Skim Result - Rail",0)
        util.initmat(eb, "mf6077", "railpr-trmtimWkMD", "PnR Lot Terminal Time - Rail",0)
        util.initmat(eb, "mf6078", "railpr-prkostWkMD", "PR parking cost - Rail",0)
        util.initmat(eb, "mf6079", "railpr-autAcsWkMD", "Auto access time  - Rail",0)
        util.initmat(eb, "mf6080", "railpr-railIVTWkMD", "Rail IVT - Rail",0)
        util.initmat(eb, "mf6081", "railpr-railWtWkMD", "Rail Wait Time - Rail",0)
        util.initmat(eb, "mf6082", "railpr-busIVTWkMD", "Bus IVT - Rail",0)
        util.initmat(eb, "mf6083", "railpr-busWtWkMD", "Bus Wait Time - Rai",0)
        util.initmat(eb, "mf6084", "railpr-bordsWkMD", "Rail Boardings",0)


        # MD WCE impedance matrices
        util.initmat(eb, "mf6095", "wcepr-GctranWkMD", "WCE PnR Generalized Cost Transit Leg",0)
        util.initmat(eb, "mf6096", "wcepr-minGCWkMD", "WCE PnR Combined Skim Result",0)
        util.initmat(eb, "mf6097", "wcepr-trmtimWkMD", "PnR Lot Terminal Time - WCE",0)
        util.initmat(eb, "mf6098", "wcepr-prkostWkMD", "PR parking cost - WCE",0)
        util.initmat(eb, "mf6099", "wcepr-autAcsWkMD", "Auto access time - WCE",0)
        util.initmat(eb, "mf6100", "wcepr-wceIVTWkMD", "WCE IVT - WCE",0)
        util.initmat(eb, "mf6101", "wcepr-wceWtWkMD", "WCE Wait Time - WCE",0)
        util.initmat(eb, "mf6102", "wcepr-railIVTWkMD", "Rail IVT - WCE",0)
        util.initmat(eb, "mf6103", "wcepr-railWtWkMD", "Rail Wait Time - WCE",0)
        util.initmat(eb, "mf6104", "wcepr-busIVTWkMD", "Bus IVT - WCE",0)
        util.initmat(eb, "mf6105", "wcepr-busWtWkMD", "Bus Wait Time - WCE",0)
        util.initmat(eb, "mf6106", "wcepr-bordsWkMD", "Boardings - WCE",0)


        # PM Auto generalized Cost same for all modes
        util.initmat(eb, "mf6108", "buspr-gcAutoWkPM", "PnR Generalized Cost Auto Leg",0)


        # PM bus impedance matrices
        util.initmat(eb, "mf6110", "buspr-GctranWkPM", "PnR Generalized Cost Transit Leg - Bus",0)
        util.initmat(eb, "mf6111", "buspr-minGCWkPM", "PnR Combined Skim Result - Bus",0)
        util.initmat(eb, "mf6112", "buspr-trmtimWkPM", "PnR Lot Terminal Time - Bus",0)
        util.initmat(eb, "mf6113", "buspr-prkostWkPM", "PR parking cost - Bus",0)
        util.initmat(eb, "mf6114", "buspr-autAcsWkPM", "Auto access time  - Bus",0)
        util.initmat(eb, "mf6115", "buspr-busIVTWkPM", "Bus IVTT - Bus",0)
        util.initmat(eb, "mf6116", "buspr-busWtWkPM", "Bus Wait Time - Bus",0)
        util.initmat(eb, "mf6117", "buspr-bordsWkPM", "Boardings - Bus",0)


        # PM rail impedance matrices
        util.initmat(eb, "mf6125", "railpr-GctranWkPM", "Rail PnR Generalized Cost Transit Leg - Rail",0)
        util.initmat(eb, "mf6126", "railpr-minGCWkPM", "Rail PnR Combined Skim Result - Rail",0)
        util.initmat(eb, "mf6127", "railpr-trmtimWkPM", "PnR Lot Terminal Time - Rail",0)
        util.initmat(eb, "mf6128", "railpr-prkostWkPM", "PR parking cost - Rail",0)
        util.initmat(eb, "mf6129", "railpr-autAcsWkPM", "Auto access time  - Rail",0)
        util.initmat(eb, "mf6130", "railpr-railIVTWkPM", "Rail IVT - Rail",0)
        util.initmat(eb, "mf6131", "railpr-railWtWkPM", "Rail Wait Time - Rail",0)
        util.initmat(eb, "mf6132", "railpr-busIVTWkPM", "Bus IVT - Rail",0)
        util.initmat(eb, "mf6133", "railpr-busWtWkPM", "Bus Wait Time - Rai",0)
        util.initmat(eb, "mf6134", "railpr-bordsWkPM", "Rail Boardings",0)


        # PM WCE impedance matrices
        util.initmat(eb, "mf6145", "wcepr-GctranWkPM", "WCE PnR Generalized Cost Transit Leg",0)
        util.initmat(eb, "mf6146", "wcepr-minGCWkPM", "WCE PnR Combined Skim Result",0)
        util.initmat(eb, "mf6147", "wcepr-trmtimWkPM", "PnR Lot Terminal Time - WCE",0)
        util.initmat(eb, "mf6148", "wcepr-prkostWkPM", "PR parking cost - WCE",0)
        util.initmat(eb, "mf6149", "wcepr-autAcsWkPM", "Auto access time - WCE",0)
        util.initmat(eb, "mf6150", "wcepr-wceIVTWkPM", "WCE IVT - WCE",0)
        util.initmat(eb, "mf6151", "wcepr-wceWtWkPM", "WCE Wait Time - WCE",0)
        util.initmat(eb, "mf6152", "wcepr-railIVTWkPM", "Rail IVT - WCE",0)
        util.initmat(eb, "mf6153", "wcepr-railWtWkPM", "Rail Wait Time - WCE",0)
        util.initmat(eb, "mf6154", "wcepr-busIVTWkPM", "Bus IVT - WCE",0)
        util.initmat(eb, "mf6155", "wcepr-busWtWkPM", "Bus Wait Time - WCE",0)
        util.initmat(eb, "mf6156", "wcepr-bordsWkPM", "Boardings - WCE",0)



        # Lot choice using AM impedances, but lot choice fixed for all time periods
        util.initmat(eb, "mf6160", "buspr-lotChceNWkAM", "Bus Best PnR Lot - Bus",0)
        util.initmat(eb, "mf6161", "railpr-lotChceNWkAM", "Rail Best PnR Lot - Rail",0)
        util.initmat(eb, "mf6162", "wcepr-lotChceNWkAM", "Rail Best PnR Lot -WCE",0)


        # AM Auto generalized Cost same for all modes
        util.initmat(eb, "mf6163", "buspr-gcAutoAM", "PnR Generalized Cost Auto Leg",0)


        # AM bus impedance matrices
        util.initmat(eb, "mf6165", "buspr-GctranNWkAM", "PnR Generalized Cost Transit Leg - Bus",0)
        util.initmat(eb, "mf6166", "buspr-minGCNWkAM", "PnR Combined Skim Result - Bus",0)
        util.initmat(eb, "mf6167", "buspr-trmtimNWkAM", "PnR Lot Terminal Time - Bus",0)
        util.initmat(eb, "mf6168", "buspr-prkostNWkAM", "PR parking cost - Bus",0)
        util.initmat(eb, "mf6169", "buspr-autAcsNWkAM", "Auto access time  - Bus",0)
        util.initmat(eb, "mf6170", "buspr-busIVTNWkAM", "Bus IVTT - Bus",0)
        util.initmat(eb, "mf6171", "buspr-busWtNWkAM", "Bus Wait Time - Bus",0)
        util.initmat(eb, "mf6172", "buspr-bordsNWkAM", "Boardings - Bus",0)


        # AM rail impedance matrices
        util.initmat(eb, "mf6180", "railpr-GctranNWkAM", "Rail PnR Generalized Cost Transit Leg - Rail",0)
        util.initmat(eb, "mf6181", "railpr-minGCNWkAM", "Rail PnR Combined Skim Result - Rail",0)
        util.initmat(eb, "mf6182", "railpr-trmtimNWkAM", "PnR Lot Terminal Time - Rail",0)
        util.initmat(eb, "mf6183", "railpr-prkostNWkAM", "PR parking cost - Rail",0)
        util.initmat(eb, "mf6184", "railpr-autAcsNWkAM", "Auto access time  - Rail",0)
        util.initmat(eb, "mf6185", "railpr-railIVTNWkAM", "Rail IVT - Rail",0)
        util.initmat(eb, "mf6186", "railpr-railWtNWkAM", "Rail Wait Time - Rail",0)
        util.initmat(eb, "mf6187", "railpr-busIVTNWkAM", "Bus IVT - Rail",0)
        util.initmat(eb, "mf6188", "railpr-busWtNWkAM", "Bus Wait Time - Rai",0)
        util.initmat(eb, "mf6189", "railpr-bordsNWkAM", "Rail Boardings",0)


        # AM WCE impedance matrices
        util.initmat(eb, "mf6200", "wcepr-GctranNWkAM", "WCE PnR Generalized Cost Transit Leg",0)
        util.initmat(eb, "mf6201", "wcepr-minGCNWkAM", "WCE PnR Combined Skim Result",0)
        util.initmat(eb, "mf6202", "wcepr-trmtimNWkAM", "PnR Lot Terminal Time - WCE",0)
        util.initmat(eb, "mf6203", "wcepr-prkostNWkAM", "PR parking cost - WCE",0)
        util.initmat(eb, "mf6204", "wcepr-autAcsNWkAM", "Auto access time - WCE",0)
        util.initmat(eb, "mf6205", "wcepr-wceIVTNWkAM", "WCE IVT - WCE",0)
        util.initmat(eb, "mf6206", "wcepr-wceWtNWkAM", "WCE Wait Time - WCE",0)
        util.initmat(eb, "mf6207", "wcepr-railIVTNWkAM", "Rail IVT - WCE",0)
        util.initmat(eb, "mf6208", "wcepr-railWtNWkAM", "Rail Wait Time - WCE",0)
        util.initmat(eb, "mf6209", "wcepr-busIVTNWkAM", "Bus IVT - WCE",0)
        util.initmat(eb, "mf6210", "wcepr-busWtNWkAM", "Bus Wait Time - WCE",0)
        util.initmat(eb, "mf6211", "wcepr-bordsNWkAM", "Boardings - WCE",0)


        # MD Auto generalized Cost same for all modes
        util.initmat(eb, "mf6213", "buspr-gcAutoNWkMD", "PnR Generalized Cost Auto Leg",0)


        # MD bus impedance matrices
        util.initmat(eb, "mf6215", "buspr-GctranNWkMD", "PnR Generalized Cost Transit Leg - Bus",0)
        util.initmat(eb, "mf6216", "buspr-minGCNWkMD", "PnR Combined Skim Result - Bus",0)
        util.initmat(eb, "mf6217", "buspr-trmtimNWkMD", "PnR Lot Terminal Time - Bus",0)
        util.initmat(eb, "mf6218", "buspr-prkostNWkMD", "PR parking cost - Bus",0)
        util.initmat(eb, "mf6219", "buspr-autAcsNWkMD", "Auto access time  - Bus",0)
        util.initmat(eb, "mf6220", "buspr-busIVTNWkMD", "Bus IVTT - Bus",0)
        util.initmat(eb, "mf6221", "buspr-busWtNWkMD", "Bus Wait Time - Bus",0)
        util.initmat(eb, "mf6222", "buspr-bordsNWkMD", "Boardings - Bus",0)


        # MD rail impedance matrices
        util.initmat(eb, "mf6230", "railpr-GctranNWkMD", "Rail PnR Generalized Cost Transit Leg - Rail",0)
        util.initmat(eb, "mf6231", "railpr-minGCNWkMD", "Rail PnR Combined Skim Result - Rail",0)
        util.initmat(eb, "mf6232", "railpr-trmtimNWkMD", "PnR Lot Terminal Time - Rail",0)
        util.initmat(eb, "mf6233", "railpr-prkostNWkMD", "PR parking cost - Rail",0)
        util.initmat(eb, "mf6234", "railpr-autAcsNWkMD", "Auto access time  - Rail",0)
        util.initmat(eb, "mf6235", "railpr-railIVTNWkMD", "Rail IVT - Rail",0)
        util.initmat(eb, "mf6236", "railpr-railWtNWkMD", "Rail Wait Time - Rail",0)
        util.initmat(eb, "mf6237", "railpr-busIVTNWkMD", "Bus IVT - Rail",0)
        util.initmat(eb, "mf6238", "railpr-busWtNWkMD", "Bus Wait Time - Rai",0)
        util.initmat(eb, "mf6239", "railpr-bordsNWkMD", "Rail Boardings",0)


        # MD WCE impedance matrices
        util.initmat(eb, "mf6250", "wcepr-GctranNWkMD", "WCE PnR Generalized Cost Transit Leg",0)
        util.initmat(eb, "mf6251", "wcepr-minGCNWkMD", "WCE PnR Combined Skim Result",0)
        util.initmat(eb, "mf6252", "wcepr-trmtimNWkMD", "PnR Lot Terminal Time - WCE",0)
        util.initmat(eb, "mf6253", "wcepr-prkostNWkMD", "PR parking cost - WCE",0)
        util.initmat(eb, "mf6254", "wcepr-autAcsNWkMD", "Auto access time - WCE",0)
        util.initmat(eb, "mf6255", "wcepr-wceIVTNWkMD", "WCE IVT - WCE",0)
        util.initmat(eb, "mf6256", "wcepr-wceWtNWkMD", "WCE Wait Time - WCE",0)
        util.initmat(eb, "mf6257", "wcepr-railIVTNWkMD", "Rail IVT - WCE",0)
        util.initmat(eb, "mf6258", "wcepr-railWtNWkMD", "Rail Wait Time - WCE",0)
        util.initmat(eb, "mf6259", "wcepr-busIVTNWkMD", "Bus IVT - WCE",0)
        util.initmat(eb, "mf6260", "wcepr-busWtNWkMD", "Bus Wait Time - WCE",0)
        util.initmat(eb, "mf6261", "wcepr-bordsNWkMD", "Boardings - WCE",0)


        # PM Auto generalized Cost same for all modes
        util.initmat(eb, "mf6263", "buspr-gcAutoNWkPM", "PnR Generalized Cost Auto Leg",0)


        # PM bus impedance matrices
        util.initmat(eb, "mf6265", "buspr-GctranNWkPM", "PnR Generalized Cost Transit Leg - Bus",0)
        util.initmat(eb, "mf6266", "buspr-minGCNWkPM", "PnR Combined Skim Result - Bus",0)
        util.initmat(eb, "mf6267", "buspr-trmtimNWkPM", "PnR Lot Terminal Time - Bus",0)
        util.initmat(eb, "mf6268", "buspr-prkostNWkPM", "PR parking cost - Bus",0)
        util.initmat(eb, "mf6269", "buspr-autAcsNWkPM", "Auto access time  - Bus",0)
        util.initmat(eb, "mf6270", "buspr-busIVTNWkPM", "Bus IVTT - Bus",0)
        util.initmat(eb, "mf6271", "buspr-busWtNWkPM", "Bus Wait Time - Bus",0)
        util.initmat(eb, "mf6272", "buspr-bordsNWkPM", "Boardings - Bus",0)


        # PM rail impedance matrices
        util.initmat(eb, "mf6280", "railpr-GctranNWkPM", "Rail PnR Generalized Cost Transit Leg - Rail",0)
        util.initmat(eb, "mf6281", "railpr-minGCNWkPM", "Rail PnR Combined Skim Result - Rail",0)
        util.initmat(eb, "mf6282", "railpr-trmtimNWkPM", "PnR Lot Terminal Time - Rail",0)
        util.initmat(eb, "mf6283", "railpr-prkostNWkPM", "PR parking cost - Rail",0)
        util.initmat(eb, "mf6284", "railpr-autAcsNWkPM", "Auto access time  - Rail",0)
        util.initmat(eb, "mf6285", "railpr-railIVTNWkPM", "Rail IVT - Rail",0)
        util.initmat(eb, "mf6286", "railpr-railWtNWkPM", "Rail Wait Time - Rail",0)
        util.initmat(eb, "mf6287", "railpr-busIVTNWkPM", "Bus IVT - Rail",0)
        util.initmat(eb, "mf6288", "railpr-busWtNWkPM", "Bus Wait Time - Rai",0)
        util.initmat(eb, "mf6289", "railpr-bordsNWkPM", "Rail Boardings",0)


        # PM WCE impedance matrices
        util.initmat(eb, "mf6300", "wcepr-GctranNWkPM", "WCE PnR Generalized Cost Transit Leg",0)
        util.initmat(eb, "mf6301", "wcepr-minGCNWkPM", "WCE PnR Combined Skim Result",0)
        util.initmat(eb, "mf6302", "wcepr-trmtimNWkPM", "PnR Lot Terminal Time - WCE",0)
        util.initmat(eb, "mf6303", "wcepr-prkostNWkPM", "PR parking cost - WCE",0)
        util.initmat(eb, "mf6304", "wcepr-autAcsNWkPM", "Auto access time - WCE",0)
        util.initmat(eb, "mf6305", "wcepr-wceIVTNWkPM", "WCE IVT - WCE",0)
        util.initmat(eb, "mf6306", "wcepr-wceWtNWkPM", "WCE Wait Time - WCE",0)
        util.initmat(eb, "mf6307", "wcepr-railIVTNWkPM", "Rail IVT - WCE",0)
        util.initmat(eb, "mf6308", "wcepr-railWtNWkPM", "Rail Wait Time - WCE",0)
        util.initmat(eb, "mf6309", "wcepr-busIVTNWkPM", "Bus IVT - WCE",0)
        util.initmat(eb, "mf6310", "wcepr-busWtNWkPM", "Bus Wait Time - WCE",0)
        util.initmat(eb, "mf6311", "wcepr-bordsNWkPM", "Boardings - WCE",0)




    @_m.logbook_trace("UNDER DEV - PNR Impedance")
    def read_file(self, eb, file):
        util = _m.Modeller().tool("translink.emme.util")
        #Read data from file and check number of lines
        with open(file, "rb") as sourcefile:
            lines = list(csv.reader(sourcefile, skipinitialspace=True))

        #TODO - validate each line has the same number of entries

        matrices = []
        mat_data = []
        # Initialize all matrices with 0-values and store a data reference
        for i in range(1, len(lines[0])):
            mat = util.initmat(eb, lines[0][i], lines[1][i], lines[2][i], 0)
            matrices.append(mat)
            mat_data.append(mat.get_data())

        # loop over each data-containing line in the csv
        for i in range(3, len(lines)):
            line = lines[i]
            # within each line set the data in each matrix
            for j in range(1, len(line)):
                mat_data[j-1].set(int(line[0]), float(line[j]))

        # store the data back into the matrix on disk
        for i in range(len(matrices)):
            matrices[i].set_data(mat_data[i])



    def AutoImpedance(self, eb):
        util = _m.Modeller().tool("translink.emme.util")
