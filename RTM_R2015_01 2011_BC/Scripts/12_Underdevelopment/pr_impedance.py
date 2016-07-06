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
        pb.description = "Calculates Impedance for PnR based on Best Lot"
        pb.branding_text = "TransLink"

        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)

        return pb.render()

    def run(self):
        with _m.logbook_trace("UNDER DEV - PR Impedance"):
            self.tool_run_msg = ""
            try:
                eb = _m.Modeller().emmebank
                self.__call__(eb)
                self.tool_run_msg = _m.PageBuilder.format_info("Tool complete")
            except Exception, e:
                self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc(e))



    @_m.logbook_trace("UNDER DEV - PNR Impedance")
    def __call__(self, eb):

        util = _m.Modeller().tool("translink.emme.util")
        input_path = util.get_input_path(eb)
        pnr_costs = os.path.join(input_path, "pnr_inputs.csv")

        #RailSkim = _m.Modeller().tool("translink.emme.under_dev.wceskim")
        # railassign = _m.Modeller().tool("inro.emme.transit_assignment.extended_transit_assignment")

        self.matrix_batchins(eb)
        self.read_file(eb, pnr_costs)

        self.AutoGT(eb)
        self.BusGT(eb)
        self.RailGT(eb)
        self.WceGT(eb)


    def WceGT(self, eb):
        util = _m.Modeller().tool("translink.emme.util")
        # [AM,MD,PM]
        transit_mats = {"wceIVT" : ["mf5052",  "mf5058", "mf5064"],
                        "wceWait" : ["mf5053",  "mf5059", "mf5065"],
                        "railIVT" : ["mf5051",  "mf5057", "mf5063"],
                        "busIVT" : ["mf5050",  "mf5056", "mf5062"],
                        "auxTransit" : ["mf5055",  "mf5061", "mf5067"],
                        "boardings" : ["mf5054",  "mf5060", "mf5066"],
                        "wceFare" : ["mf161",  "mf161", "mf161"]}

        # [Work, non-work]
        vot_mats = ['msvotWkmed', 'msvotNWkmed']

        # [[AMWk, MDWk, PMWk],[AMnonWk, MDnonWk, PMnonWk]]
        result_mats = [["mf6030",  "mf6075", "mf6115"],["mf6160",  "mf6200", "mf6240"]]

        #calculate generalized time for bus leg
        specs = []
        for i in range(0,3):
            for j in range(0,2):
                expression = ("{wceIVT} * {wceIVTprcp}"
                              " + {wceWait} * {wceOVTprcp}"
                              " + {railIVT} * {railIVTprcp}"
                              " + {busIVT} * {busIVTprcp}"
                              " + {auxTrans} * {walkprcp}"
                              " + {boardings} * {transferprcp} "
                              " + {fare} * {VOT}"
                              ).format(wceIVT=transit_mats["wceIVT"][i],
                                       wceWait=transit_mats["wceWait"][i],
                                       railIVT=transit_mats["railIVT"][i],
                                       busIVT=transit_mats["busIVT"][i],
                                       auxTrans=transit_mats["auxTransit"][i],
                                       boardings=transit_mats["boardings"][i],
                                       fare=transit_mats["wceFare"][i],
                                       wceIVTprcp="mswceIVTprcp",
                                       wceOVTprcp="mswceOVTprcp",
                                       railIVTprcp="msrailIVTprcp",
                                       busIVTprcp="msbusIVTprcp",
                                       walkprcp="mswalkprcp",
                                       transferprcp="mswceTRANSprcp",
                                       VOT=vot_mats[j])

                result = ("{wceGT}").format(wceGT=result_mats[j][i])
                specs.append(util.matrix_spec(result, expression))
        util.compute_matrix(specs)



    def RailGT(self, eb):
        util = _m.Modeller().tool("translink.emme.util")
        # [AM,MD,PM]
        transit_mats = {"railIVT" : ["mf5001",  "mf5006", "mf5011"],
                        "railWait" : ["mf5002",  "mf5007", "mf5012"],
                        "busIVT" : ["mf5000",  "mf5005", "mf5010"],
                        "auxTransit" : ["mf5004", "mf5009", "mf5014"],
                        "boardings" : ["mf5003", "mf5008", "mf5014"],
                        "railFare" : ["mf161",  "mf161", "mf161"]}

        # [Work, non-work]
        vot_mats = ['msvotWkmed', 'msvotNWkmed']

        # [[AMWk, MDWk, PMWk],[AMnonWk, MDnonWk, PMnonWk]]
        result_mats = [["mf6015", "mf6060", "mf6100"],['mf6145','mf6185','mf6225']]

        #calculate generalized time for bus leg
        specs = []
        for i in range(0,3):
            for j in range(0,2):
                expression = ("{railIVT} * {railIVTprcp}"
                              " + {railWait} * {railOVTprcp}"
                              " + {busIVT} * {busIVTprcp}"
                              " + {auxTrans} * {walkprcp}"
                              " + {boardings} * {transferprcp} "
                              " + {fare} * {VOT}"
                              ).format(railIVT=transit_mats["railIVT"][i],
                                       railWait=transit_mats["railWait"][i],
                                       busIVT=transit_mats["busIVT"][i],
                                       auxTrans=transit_mats["auxTransit"][i],
                                       boardings=transit_mats["boardings"][i],
                                       fare=transit_mats["railFare"][i],
                                       railIVTprcp="msrailIVTprcp",
                                       railOVTprcp="msrailOVTprcp",
                                       busIVTprcp="msbusIVTprcp",
                                       walkprcp="mswalkprcp",
                                       transferprcp="msrailTRANSprcp",
                                       VOT=vot_mats[j])

                result = ("{railGT}").format(railGT=result_mats[j][i])
                specs.append(util.matrix_spec(result, expression))
        util.compute_matrix(specs)



    def BusGT(self, eb):
        util = _m.Modeller().tool("translink.emme.util")
        # [AM,MD,PM]
        transit_mats = {"busIVT" : ["mf107",  "mf112", "mf2107"],
                        "busWait" : ["mf106",  "mf111", "mf2106"],
                        "auxTransit" : ["mf109", "mf114", "mf2109"],
                        "boardings" : ["mf108", "mf113", "mf2108"],
                        "busFare" : ["mf160",  "mf160", "mf160"]}

        # [Work, non-work]
        vot_mats = ['msvotWkmed', 'msvotNWkmed']

        # [[AMWk, MDWk, PMWk],[AMnonWk, MDnonWk, PMnonWk]]
        result_mats = [["mf6005", "mf6050", "mf6090"],['mf6135','mf6175','mf6215']]

        #calculate generalized time for bus leg
        specs = []
        for i in range(0,3):
            for j in range(0,2):
                expression = ("{busIVT} * {busIVTprcp}"
                              " + {busWait} * {busOVTprcp}"
                              " + {auxTrans} * {walkprcp}"
                              " + {boardings} * {transferprcp} "
                              " + {fare} * {VOT}"
                              ).format(busIVT=transit_mats["busIVT"][i],
                                       busWait=transit_mats["busWait"][i],
                                       auxTrans=transit_mats["auxTransit"][i],
                                       boardings=transit_mats["boardings"][i],
                                       busFare=transit_mats["busFare"][i],
                                       busIVTprcp="msbusIVTprcp",
                                       busOVTprcp="msbusOVTprcp",
                                       walkprcp="mswalkprcp",
                                       transferprcp="msbusTRANSprcp",
                                       VOT=vot_mats[j])

                result = ("{busGT}").format(busGT=result_mats[j][i])
                specs.append(util.matrix_spec(result, expression))
        util.compute_matrix(specs)



    def AutoGT(self, eb):
        util = _m.Modeller().tool("translink.emme.util")
        # [AM,MD,PM]
        auto_mats = {"autotime" : ["mf101",  "mf104", "mf2101"],
                    "autotoll" : ["mf102", "mf105", "mf2102"],
                    "autodist" : ["mf100", "mf103", "mf2100"] }

        # [Work, non-work]
        vot_mats = ['msvotWkmed', 'msvotNWkmed']

        # [[AMWk, MDWk, PMWk],[AMnonWk, MDnonWk, PMnonWk]]
        result_mats = [["mf6003", "mf6048", "mf6088"],['mf6133','mf6173','mf6213']]

        specs = []
        for i in range(0,3):
            for j in range(0,2):
                expression = ("{autotime} + {termtime}"
                              " + (({VOC} * {autodist}) + {autotoll} + {lotcost}) * {VOT}"
                              ).format(autotime=auto_mats["autotime"][i],
                                       autotoll=auto_mats["autotoll"][i],
                                       autodist=auto_mats["autodist"][i],
                                       VOT=vot_mats[j],
                                       VOC="msVOC",
                                       lotcost = "mdPRcost",
                                       termtime = "mdPRtermtime")

                result = ("{autoGT}").format(autoGT=result_mats[j][i])
                specs.append(util.matrix_spec(result, expression))
        util.compute_matrix(specs)



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

        util.initmat(eb,"ms130", "VOC", "Vehicle Operating Variable Cost (/km)", 0.18) # CAA includes fuel, tires, maintence

        # transit scalars
        #TODO update these factors to actual values
        util.initmat(eb, "ms199", "walkprcp", "walk time perception factor", 1)

        util.initmat(eb, "ms200", "busIVTprcp", "bus IVT perception factor", 1)
        util.initmat(eb, "ms201", "busOVTprcp", "bus OVT perception factor", 1.5)
        util.initmat(eb, "ms202", "busTRANSprcp", "bus transfer perception factor", 5)

        util.initmat(eb, "ms205", "railIVTprcp", "rail IVT perception factor", 1)
        util.initmat(eb, "ms206", "railOVTprcp", "rail OVT perception factor", 1.5)
        util.initmat(eb, "ms207", "railTRANSprcp", "rail transfer perception factor", 5)

        util.initmat(eb, "ms210", "wceIVTprcp", "wce IVT perception factor", 1)
        util.initmat(eb, "ms211", "wceOVTprcp", "wce OVT perception factor", 1.5)
        util.initmat(eb, "ms212", "wceTRANSprcp", "wce transfer perception factor", 5)

        # Lot choice using AM impedances, but lot choice fixed for all time periods
        util.initmat(eb, "mf6000", "buspr-lotChceWkAM", "Bus Best PnR Lot - Bus",0)
        util.initmat(eb, "mf6001", "railpr-lotChceWkAM", "Rail Best PnR Lot - Rail",0)
        util.initmat(eb, "mf6002", "wcepr-lotChceWkAM", "Rail Best PnR Lot -WCE",0)


        # AM Auto generalized Cost same for all modes
        util.initmat(eb, "mf6003", "pr-gtAutoWkAM", "PnR Generalized Cost Auto Leg",0)


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
        util.initmat(eb, "mf6015", "railpr-GctranWkAM", "Rail PnR Generalized Cost Transit Leg - Rail",0)
        util.initmat(eb, "mf6016", "railpr-minGCWkAM", "Rail PnR Combined Skim Result - Rail",0)
        util.initmat(eb, "mf6017", "railpr-trmtimWkAM", "PnR Lot Terminal Time - Rail",0)
        util.initmat(eb, "mf6018", "railpr-prkostWkAM", "PR parking cost - Rail",0)
        util.initmat(eb, "mf6019", "railpr-autAcsWkAM", "Auto access time  - Rail",0)
        util.initmat(eb, "mf6020", "railpr-railIVTWkAM", "Rail IVT - Rail",0)
        util.initmat(eb, "mf6021", "railpr-railWtWkAM", "Rail Wait Time - Rail",0)
        util.initmat(eb, "mf6022", "railpr-busIVTWkAM", "Bus IVT - Rail",0)
        util.initmat(eb, "mf6023", "railpr-busWtWkAM", "Bus Wait Time - Rai",0)
        util.initmat(eb, "mf6024", "railpr-bordsWkAM", "Rail Boardings",0)


        # AM WCE impedance matrices
        util.initmat(eb, "mf6030", "wcepr-GctranWkAM", "WCE PnR Generalized Cost Transit Leg",0)
        util.initmat(eb, "mf6031", "wcepr-minGCWkAM", "WCE PnR Combined Skim Result",0)
        util.initmat(eb, "mf6032", "wcepr-trmtimWkAM", "PnR Lot Terminal Time - WCE",0)
        util.initmat(eb, "mf6033", "wcepr-prkostWkAM", "PR parking cost - WCE",0)
        util.initmat(eb, "mf6034", "wcepr-autAcsWkAM", "Auto access time - WCE",0)
        util.initmat(eb, "mf6035", "wcepr-wceIVTWkAM", "WCE IVT - WCE",0)
        util.initmat(eb, "mf6036", "wcepr-wceWtWkAM", "WCE Wait Time - WCE",0)
        util.initmat(eb, "mf6037", "wcepr-railIVTWkAM", "Rail IVT - WCE",0)
        util.initmat(eb, "mf6038", "wcepr-railWtWkAM", "Rail Wait Time - WCE",0)
        util.initmat(eb, "mf6039", "wcepr-busIVTWkAM", "Bus IVT - WCE",0)
        util.initmat(eb, "mf6040", "wcepr-busWtWkAM", "Bus Wait Time - WCE",0)
        util.initmat(eb, "mf6041", "wcepr-bordsWkAM", "Boardings - WCE",0)


        # MD Auto generalized Cost same for all modes
        util.initmat(eb, "mf6048", "pr-gtAutoWkMD", "PnR Generalized Cost Auto Leg",0)


        # MD bus impedance matrices
        util.initmat(eb, "mf6050", "buspr-GctranWkMD", "PnR Generalized Cost Transit Leg - Bus",0)
        util.initmat(eb, "mf6051", "buspr-minGCWkMD", "PnR Combined Skim Result - Bus",0)
        util.initmat(eb, "mf6052", "buspr-trmtimWkMD", "PnR Lot Terminal Time - Bus",0)
        util.initmat(eb, "mf6053", "buspr-prkostWkMD", "PR parking cost - Bus",0)
        util.initmat(eb, "mf6054", "buspr-autAcsWkMD", "Auto access time  - Bus",0)
        util.initmat(eb, "mf6055", "buspr-busIVTWkMD", "Bus IVTT - Bus",0)
        util.initmat(eb, "mf6056", "buspr-busWtWkMD", "Bus Wait Time - Bus",0)
        util.initmat(eb, "mf6057", "buspr-bordsWkMD", "Boardings - Bus",0)


        # MD rail impedance matrices
        util.initmat(eb, "mf6060", "railpr-GctranWkMD", "Rail PnR Generalized Cost Transit Leg - Rail",0)
        util.initmat(eb, "mf6061", "railpr-minGCWkMD", "Rail PnR Combined Skim Result - Rail",0)
        util.initmat(eb, "mf6062", "railpr-trmtimWkMD", "PnR Lot Terminal Time - Rail",0)
        util.initmat(eb, "mf6063", "railpr-prkostWkMD", "PR parking cost - Rail",0)
        util.initmat(eb, "mf6064", "railpr-autAcsWkMD", "Auto access time  - Rail",0)
        util.initmat(eb, "mf6065", "railpr-railIVTWkMD", "Rail IVT - Rail",0)
        util.initmat(eb, "mf6066", "railpr-railWtWkMD", "Rail Wait Time - Rail",0)
        util.initmat(eb, "mf6067", "railpr-busIVTWkMD", "Bus IVT - Rail",0)
        util.initmat(eb, "mf6068", "railpr-busWtWkMD", "Bus Wait Time - Rai",0)
        util.initmat(eb, "mf6069", "railpr-bordsWkMD", "Rail Boardings",0)


        # MD WCE impedance matrices
        util.initmat(eb, "mf6075", "wcepr-GctranWkMD", "WCE PnR Generalized Cost Transit Leg",0)
        util.initmat(eb, "mf6076", "wcepr-minGCWkMD", "WCE PnR Combined Skim Result",0)
        util.initmat(eb, "mf6077", "wcepr-trmtimWkMD", "PnR Lot Terminal Time - WCE",0)
        util.initmat(eb, "mf6078", "wcepr-prkostWkMD", "PR parking cost - WCE",0)
        util.initmat(eb, "mf6079", "wcepr-autAcsWkMD", "Auto access time - WCE",0)
        util.initmat(eb, "mf6080", "wcepr-wceIVTWkMD", "WCE IVT - WCE",0)
        util.initmat(eb, "mf6081", "wcepr-wceWtWkMD", "WCE Wait Time - WCE",0)
        util.initmat(eb, "mf6082", "wcepr-railIVTWkMD", "Rail IVT - WCE",0)
        util.initmat(eb, "mf6083", "wcepr-railWtWkMD", "Rail Wait Time - WCE",0)
        util.initmat(eb, "mf6084", "wcepr-busIVTWkMD", "Bus IVT - WCE",0)
        util.initmat(eb, "mf6085", "wcepr-busWtWkMD", "Bus Wait Time - WCE",0)
        util.initmat(eb, "mf6086", "wcepr-bordsWkMD", "Boardings - WCE",0)


        # PM Auto generalized Cost same for all modes
        util.initmat(eb, "mf6088", "pr-gtAutoWkPM", "PnR Generalized Cost Auto Leg",0)


        # PM bus impedance matrices
        util.initmat(eb, "mf6090", "buspr-GctranWkPM", "PnR Generalized Cost Transit Leg - Bus",0)
        util.initmat(eb, "mf6091", "buspr-minGCWkPM", "PnR Combined Skim Result - Bus",0)
        util.initmat(eb, "mf6092", "buspr-trmtimWkPM", "PnR Lot Terminal Time - Bus",0)
        util.initmat(eb, "mf6093", "buspr-prkostWkPM", "PR parking cost - Bus",0)
        util.initmat(eb, "mf6094", "buspr-autAcsWkPM", "Auto access time  - Bus",0)
        util.initmat(eb, "mf6095", "buspr-busIVTWkPM", "Bus IVTT - Bus",0)
        util.initmat(eb, "mf6096", "buspr-busWtWkPM", "Bus Wait Time - Bus",0)
        util.initmat(eb, "mf6097", "buspr-bordsWkPM", "Boardings - Bus",0)


        # PM rail impedance matrices
        util.initmat(eb, "mf6100", "railpr-GctranWkPM", "Rail PnR Generalized Cost Transit Leg - Rail",0)
        util.initmat(eb, "mf6101", "railpr-minGCWkPM", "Rail PnR Combined Skim Result - Rail",0)
        util.initmat(eb, "mf6102", "railpr-trmtimWkPM", "PnR Lot Terminal Time - Rail",0)
        util.initmat(eb, "mf6103", "railpr-prkostWkPM", "PR parking cost - Rail",0)
        util.initmat(eb, "mf6104", "railpr-autAcsWkPM", "Auto access time  - Rail",0)
        util.initmat(eb, "mf6105", "railpr-railIVTWkPM", "Rail IVT - Rail",0)
        util.initmat(eb, "mf6106", "railpr-railWtWkPM", "Rail Wait Time - Rail",0)
        util.initmat(eb, "mf6107", "railpr-busIVTWkPM", "Bus IVT - Rail",0)
        util.initmat(eb, "mf6108", "railpr-busWtWkPM", "Bus Wait Time - Rai",0)
        util.initmat(eb, "mf6109", "railpr-bordsWkPM", "Rail Boardings",0)


        # PM WCE impedance matrices
        util.initmat(eb, "mf6115", "wcepr-GctranWkPM", "WCE PnR Generalized Cost Transit Leg",0)
        util.initmat(eb, "mf6116", "wcepr-minGCWkPM", "WCE PnR Combined Skim Result",0)
        util.initmat(eb, "mf6117", "wcepr-trmtimWkPM", "PnR Lot Terminal Time - WCE",0)
        util.initmat(eb, "mf6118", "wcepr-prkostWkPM", "PR parking cost - WCE",0)
        util.initmat(eb, "mf6119", "wcepr-autAcsWkPM", "Auto access time - WCE",0)
        util.initmat(eb, "mf6120", "wcepr-wceIVTWkPM", "WCE IVT - WCE",0)
        util.initmat(eb, "mf6121", "wcepr-wceWtWkPM", "WCE Wait Time - WCE",0)
        util.initmat(eb, "mf6122", "wcepr-railIVTWkPM", "Rail IVT - WCE",0)
        util.initmat(eb, "mf6123", "wcepr-railWtWkPM", "Rail Wait Time - WCE",0)
        util.initmat(eb, "mf6124", "wcepr-busIVTWkPM", "Bus IVT - WCE",0)
        util.initmat(eb, "mf6125", "wcepr-busWtWkPM", "Bus Wait Time - WCE",0)
        util.initmat(eb, "mf6126", "wcepr-bordsWkPM", "Boardings - WCE",0)



        # Lot choice using AM impedances, but lot choice fixed for all time periods
        util.initmat(eb, "mf6130", "buspr-lotChceNWkAM", "Bus Best PnR Lot - Bus",0)
        util.initmat(eb, "mf6131", "railpr-lotChceNWkAM", "Rail Best PnR Lot - Rail",0)
        util.initmat(eb, "mf6132", "wcepr-lotChceNWkAM", "Rail Best PnR Lot -WCE",0)


        # AM Auto generalized Cost same for all modes
        util.initmat(eb, "mf6133", "pr-gtAutoNWkAM", "PnR Generalized Cost Auto Leg",0)


        # AM bus impedance matrices
        util.initmat(eb, "mf6135", "buspr-GctranNWkAM", "PnR Generalized Cost Transit Leg - Bus",0)
        util.initmat(eb, "mf6136", "buspr-minGCNWkAM", "PnR Combined Skim Result - Bus",0)
        util.initmat(eb, "mf6137", "buspr-trmtimNWkAM", "PnR Lot Terminal Time - Bus",0)
        util.initmat(eb, "mf6138", "buspr-prkostNWkAM", "PR parking cost - Bus",0)
        util.initmat(eb, "mf6139", "buspr-autAcsNWkAM", "Auto access time  - Bus",0)
        util.initmat(eb, "mf6140", "buspr-busIVTNWkAM", "Bus IVTT - Bus",0)
        util.initmat(eb, "mf6141", "buspr-busWtNWkAM", "Bus Wait Time - Bus",0)
        util.initmat(eb, "mf6142", "buspr-bordsNWkAM", "Boardings - Bus",0)


        # AM rail impedance matrices
        util.initmat(eb, "mf6145", "railpr-GctranNWkAM", "Rail PnR Generalized Cost Transit Leg - Rail",0)
        util.initmat(eb, "mf6146", "railpr-minGCNWkAM", "Rail PnR Combined Skim Result - Rail",0)
        util.initmat(eb, "mf6147", "railpr-trmtimNWkAM", "PnR Lot Terminal Time - Rail",0)
        util.initmat(eb, "mf6148", "railpr-prkostNWkAM", "PR parking cost - Rail",0)
        util.initmat(eb, "mf6149", "railpr-autAcsNWkAM", "Auto access time  - Rail",0)
        util.initmat(eb, "mf6150", "railpr-railIVTNWkAM", "Rail IVT - Rail",0)
        util.initmat(eb, "mf6151", "railpr-railWtNWkAM", "Rail Wait Time - Rail",0)
        util.initmat(eb, "mf6152", "railpr-busIVTNWkAM", "Bus IVT - Rail",0)
        util.initmat(eb, "mf6153", "railpr-busWtNWkAM", "Bus Wait Time - Rai",0)
        util.initmat(eb, "mf6154", "railpr-bordsNWkAM", "Rail Boardings",0)


        # AM WCE impedance matrices
        util.initmat(eb, "mf6160", "wcepr-GctranNWkAM", "WCE PnR Generalized Cost Transit Leg",0)
        util.initmat(eb, "mf6161", "wcepr-minGCNWkAM", "WCE PnR Combined Skim Result",0)
        util.initmat(eb, "mf6162", "wcepr-trmtimNWkAM", "PnR Lot Terminal Time - WCE",0)
        util.initmat(eb, "mf6163", "wcepr-prkostNWkAM", "PR parking cost - WCE",0)
        util.initmat(eb, "mf6164", "wcepr-autAcsNWkAM", "Auto access time - WCE",0)
        util.initmat(eb, "mf6165", "wcepr-wceIVTNWkAM", "WCE IVT - WCE",0)
        util.initmat(eb, "mf6166", "wcepr-wceWtNWkAM", "WCE Wait Time - WCE",0)
        util.initmat(eb, "mf6167", "wcepr-railIVTNWkAM", "Rail IVT - WCE",0)
        util.initmat(eb, "mf6168", "wcepr-railWtNWkAM", "Rail Wait Time - WCE",0)
        util.initmat(eb, "mf6169", "wcepr-busIVTNWkAM", "Bus IVT - WCE",0)
        util.initmat(eb, "mf6170", "wcepr-busWtNWkAM", "Bus Wait Time - WCE",0)
        util.initmat(eb, "mf6171", "wcepr-bordsNWkAM", "Boardings - WCE",0)


        # MD Auto generalized Cost same for all modes
        util.initmat(eb, "mf6173", "pr-gtAutoNWkMD", "PnR Generalized Cost Auto Leg",0)


        # MD bus impedance matrices
        util.initmat(eb, "mf6175", "buspr-GctranNWkMD", "PnR Generalized Cost Transit Leg - Bus",0)
        util.initmat(eb, "mf6176", "buspr-minGCNWkMD", "PnR Combined Skim Result - Bus",0)
        util.initmat(eb, "mf6177", "buspr-trmtimNWkMD", "PnR Lot Terminal Time - Bus",0)
        util.initmat(eb, "mf6178", "buspr-prkostNWkMD", "PR parking cost - Bus",0)
        util.initmat(eb, "mf6179", "buspr-autAcsNWkMD", "Auto access time  - Bus",0)
        util.initmat(eb, "mf6180", "buspr-busIVTNWkMD", "Bus IVTT - Bus",0)
        util.initmat(eb, "mf6181", "buspr-busWtNWkMD", "Bus Wait Time - Bus",0)
        util.initmat(eb, "mf6182", "buspr-bordsNWkMD", "Boardings - Bus",0)


        # MD rail impedance matrices
        util.initmat(eb, "mf6185", "railpr-GctranNWkMD", "Rail PnR Generalized Cost Transit Leg - Rail",0)
        util.initmat(eb, "mf6186", "railpr-minGCNWkMD", "Rail PnR Combined Skim Result - Rail",0)
        util.initmat(eb, "mf6187", "railpr-trmtimNWkMD", "PnR Lot Terminal Time - Rail",0)
        util.initmat(eb, "mf6188", "railpr-prkostNWkMD", "PR parking cost - Rail",0)
        util.initmat(eb, "mf6189", "railpr-autAcsNWkMD", "Auto access time  - Rail",0)
        util.initmat(eb, "mf6190", "railpr-railIVTNWkMD", "Rail IVT - Rail",0)
        util.initmat(eb, "mf6191", "railpr-railWtNWkMD", "Rail Wait Time - Rail",0)
        util.initmat(eb, "mf6192", "railpr-busIVTNWkMD", "Bus IVT - Rail",0)
        util.initmat(eb, "mf6193", "railpr-busWtNWkMD", "Bus Wait Time - Rai",0)
        util.initmat(eb, "mf6194", "railpr-bordsNWkMD", "Rail Boardings",0)


        # MD WCE impedance matrices
        util.initmat(eb, "mf6200", "wcepr-GctranNWkMD", "WCE PnR Generalized Cost Transit Leg",0)
        util.initmat(eb, "mf6201", "wcepr-minGCNWkMD", "WCE PnR Combined Skim Result",0)
        util.initmat(eb, "mf6202", "wcepr-trmtimNWkMD", "PnR Lot Terminal Time - WCE",0)
        util.initmat(eb, "mf6203", "wcepr-prkostNWkMD", "PR parking cost - WCE",0)
        util.initmat(eb, "mf6204", "wcepr-autAcsNWkMD", "Auto access time - WCE",0)
        util.initmat(eb, "mf6205", "wcepr-wceIVTNWkMD", "WCE IVT - WCE",0)
        util.initmat(eb, "mf6206", "wcepr-wceWtNWkMD", "WCE Wait Time - WCE",0)
        util.initmat(eb, "mf6207", "wcepr-railIVTNWkMD", "Rail IVT - WCE",0)
        util.initmat(eb, "mf6208", "wcepr-railWtNWkMD", "Rail Wait Time - WCE",0)
        util.initmat(eb, "mf6209", "wcepr-busIVTNWkMD", "Bus IVT - WCE",0)
        util.initmat(eb, "mf6210", "wcepr-busWtNWkMD", "Bus Wait Time - WCE",0)
        util.initmat(eb, "mf6211", "wcepr-bordsNWkMD", "Boardings - WCE",0)


        # PM Auto generalized Cost same for all modes
        util.initmat(eb, "mf6213", "pr-gtAutoNWkPM", "PnR Generalized Cost Auto Leg",0)


        # PM bus impedance matrices
        util.initmat(eb, "mf6215", "buspr-GctranNWkPM", "PnR Generalized Cost Transit Leg - Bus",0)
        util.initmat(eb, "mf6216", "buspr-minGCNWkPM", "PnR Combined Skim Result - Bus",0)
        util.initmat(eb, "mf6217", "buspr-trmtimNWkPM", "PnR Lot Terminal Time - Bus",0)
        util.initmat(eb, "mf6218", "buspr-prkostNWkPM", "PR parking cost - Bus",0)
        util.initmat(eb, "mf6219", "buspr-autAcsNWkPM", "Auto access time  - Bus",0)
        util.initmat(eb, "mf6220", "buspr-busIVTNWkPM", "Bus IVTT - Bus",0)
        util.initmat(eb, "mf6221", "buspr-busWtNWkPM", "Bus Wait Time - Bus",0)
        util.initmat(eb, "mf6222", "buspr-bordsNWkPM", "Boardings - Bus",0)
