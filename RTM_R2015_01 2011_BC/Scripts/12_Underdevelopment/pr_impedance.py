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

        util.initmat(eb,"ms120","votWklow", "work VOT low income in min/$", 6)
        util.initmat(eb,"ms121","votWkmed", "work VOT med income in min/$", 4)
        util.initmat(eb,"ms122","votWkhigh", "work VOT high income in min/$", 3)
        util.initmat(eb,"ms123","votNWklow", "non-work VOT low income in min/$", 12)
        util.initmat(eb,"ms124","votNWkmed", "non-work VOT med income in min/$", 8)
        util.initmat(eb,"ms125","votNWkhigh", "non-work VOT high income in min/$", 6)

        util.initmat(eb,"ms130", "VOC", "Vehicle Operating Variable Cost (/km)", 0.1646) # CAA includes fuel, tires, maintence

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
        util.initmat(eb, "mf6058", "buspr-gcAutoWkPM", "PnR Generalized Cost Auto Leg",0)


        # PM bus impedance matrices
        util.initmat(eb, "mf6060", "buspr-GctranWkPM", "PnR Generalized Cost Transit Leg - Bus",0)
        util.initmat(eb, "mf6061", "buspr-minGCWkPM", "PnR Combined Skim Result - Bus",0)
        util.initmat(eb, "mf6062", "buspr-trmtimWkPM", "PnR Lot Terminal Time - Bus",0)
        util.initmat(eb, "mf6063", "buspr-prkostWkPM", "PR parking cost - Bus",0)
        util.initmat(eb, "mf6064", "buspr-autAcsWkPM", "Auto access time  - Bus",0)
        util.initmat(eb, "mf6065", "buspr-busIVTWkPM", "Bus IVTT - Bus",0)
        util.initmat(eb, "mf6066", "buspr-busWtWkPM", "Bus Wait Time - Bus",0)
        util.initmat(eb, "mf6067", "buspr-bordsWkPM", "Boardings - Bus",0)


        # PM rail impedance matrices
        util.initmat(eb, "mf6075", "railpr-GctranWkPM", "Rail PnR Generalized Cost Transit Leg - Rail",0)
        util.initmat(eb, "mf6076", "railpr-minGCWkPM", "Rail PnR Combined Skim Result - Rail",0)
        util.initmat(eb, "mf6077", "railpr-trmtimWkPM", "PnR Lot Terminal Time - Rail",0)
        util.initmat(eb, "mf6078", "railpr-prkostWkPM", "PR parking cost - Rail",0)
        util.initmat(eb, "mf6079", "railpr-autAcsWkPM", "Auto access time  - Rail",0)
        util.initmat(eb, "mf6080", "railpr-railIVTWkPM", "Rail IVT - Rail",0)
        util.initmat(eb, "mf6081", "railpr-railWtWkPM", "Rail Wait Time - Rail",0)
        util.initmat(eb, "mf6082", "railpr-busIVTWkPM", "Bus IVT - Rail",0)
        util.initmat(eb, "mf6083", "railpr-busWtWkPM", "Bus Wait Time - Rai",0)
        util.initmat(eb, "mf6084", "railpr-bordsWkPM", "Rail Boardings",0)


        # PM WCE impedance matrices
        util.initmat(eb, "mf6095", "wcepr-GctranWkPM", "WCE PnR Generalized Cost Transit Leg",0)
        util.initmat(eb, "mf6096", "wcepr-minGCWkPM", "WCE PnR Combined Skim Result",0)
        util.initmat(eb, "mf6097", "wcepr-trmtimWkPM", "PnR Lot Terminal Time - WCE",0)
        util.initmat(eb, "mf6098", "wcepr-prkostWkPM", "PR parking cost - WCE",0)
        util.initmat(eb, "mf6099", "wcepr-autAcsWkPM", "Auto access time - WCE",0)
        util.initmat(eb, "mf6100", "wcepr-wceIVTWkPM", "WCE IVT - WCE",0)
        util.initmat(eb, "mf6101", "wcepr-wceWtWkPM", "WCE Wait Time - WCE",0)
        util.initmat(eb, "mf6102", "wcepr-railIVTWkPM", "Rail IVT - WCE",0)
        util.initmat(eb, "mf6103", "wcepr-railWtWkPM", "Rail Wait Time - WCE",0)
        util.initmat(eb, "mf6104", "wcepr-busIVTWkPM", "Bus IVT - WCE",0)
        util.initmat(eb, "mf6105", "wcepr-busWtWkPM", "Bus Wait Time - WCE",0)
        util.initmat(eb, "mf6106", "wcepr-bordsWkPM", "Boardings - WCE",0)


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
