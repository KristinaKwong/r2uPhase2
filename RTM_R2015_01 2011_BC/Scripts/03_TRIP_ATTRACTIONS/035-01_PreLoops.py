##---------------------------------------------------------------------
##--TransLink Phase 3 Regional Transportation Model
##--
##--Path: translink.emme.stage2.step3.preloops
##--Purpose: Move starting skims where needed
##---------------------------------------------------------------------
import inro.modeller as _m
import os
import traceback as _traceback

class PreLoop(_m.Tool()):
    ##Create global attributes (referring to dialogue boxes on the pages)
    tool_run_msg = _m.Attribute(unicode)

    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Pre Loops"
        pb.description = "Batches in required matrices for distribution and mode choice and copies initial skims "
        pb.branding_text = "TransLink"

        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)

        return pb.render()

    def run(self):
        self.tool_run_msg = ""

        try:
            self.__call__(_m.Modeller().emmebank)
            self.tool_run_msg = _m.PageBuilder.format_info("Tool completed")
        except Exception, e:
            self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc(e))

    @_m.logbook_trace("035-01 - PRELOOPS")
    def __call__(self, eb):
        util = _m.Modeller().tool("translink.emme.util")

        util.initmat(eb, "mf210", "iWkL", "Home-work Low Inc Impedance", 0)
        util.initmat(eb, "mf211", "iWkM", "Home-work Med Inc Impedance", 0)
        util.initmat(eb, "mf212", "iWkH", "Home-work High Inc Impedance", 0)
        util.initmat(eb, "mf213", "iUv", "Home-Uni Impedance", 0)
        util.initmat(eb, "mf214", "iSc", "Home-Sch Impedance", 0)
        util.initmat(eb, "mf215", "iSh", "Home-Sho Impedance", 0)
        util.initmat(eb, "mf216", "iPB", "Home-PerBus Impedance", 0)
        util.initmat(eb, "mf217", "iSo", "Home-SocRec Impedance", 0)
        util.initmat(eb, "mf218", "iEc", "Home-Esc Impedance", 0)
        util.initmat(eb, "mf219", "iNw", "Non-home-work Impedance", 0)
        util.initmat(eb, "mf220", "iNo", "Non-home-other Impedance", 0)
        util.initmat(eb, "mf241", "g110", "P-A Distribution WkLA0", 0)
        util.initmat(eb, "mf242", "g111", "P-A Distribution WkLA1", 0)
        util.initmat(eb, "mf243", "g112", "P-A Distribution WkLA2+", 0)
        util.initmat(eb, "mf244", "g120", "P-A Distribution WkMA0", 0)
        util.initmat(eb, "mf245", "g121", "P-A Distribution WkMA1", 0)
        util.initmat(eb, "mf246", "g122", "P-A Distribution WkMA2+", 0)
        util.initmat(eb, "mf247", "g130", "P-A Distribution WkHA0", 0)
        util.initmat(eb, "mf248", "g131", "P-A Distribution WkHA1", 0)
        util.initmat(eb, "mf249", "g132", "P-A Distribution WkHA2+", 0)
        util.initmat(eb, "mf250", "g210", "P-A Distribution UvLA0", 0)
        util.initmat(eb, "mf251", "g211", "P-A Distribution UvLA1", 0)
        util.initmat(eb, "mf252", "g212", "P-A Distribution UvLA2+", 0)
        util.initmat(eb, "mf253", "g220", "P-A Distribution UvMA0", 0)
        util.initmat(eb, "mf254", "g221", "P-A Distribution UvMA1", 0)
        util.initmat(eb, "mf255", "g222", "P-A Distribution UvMA2+", 0)
        util.initmat(eb, "mf256", "g230", "P-A Distribution UvHA0", 0)
        util.initmat(eb, "mf257", "g231", "P-A Distribution UvHA1", 0)
        util.initmat(eb, "mf258", "g232", "P-A Distribution UvHA2+", 0)
        util.initmat(eb, "mf259", "g310", "P-A Distribution ScLA0", 0)
        util.initmat(eb, "mf260", "g311", "P-A Distribution ScLA1", 0)
        util.initmat(eb, "mf261", "g312", "P-A Distribution ScLA2+", 0)
        util.initmat(eb, "mf262", "g320", "P-A Distribution ScMA0", 0)
        util.initmat(eb, "mf263", "g321", "P-A Distribution ScMA1", 0)
        util.initmat(eb, "mf264", "g322", "P-A Distribution ScMA2+", 0)
        util.initmat(eb, "mf265", "g330", "P-A Distribution ScHA0", 0)
        util.initmat(eb, "mf266", "g331", "P-A Distribution ScHA1", 0)
        util.initmat(eb, "mf267", "g332", "P-A Distribution ScHA2+", 0)
        util.initmat(eb, "mf268", "g410", "P-A Distribution ShLA0", 0)
        util.initmat(eb, "mf269", "g411", "P-A Distribution ShLA1", 0)
        util.initmat(eb, "mf270", "g412", "P-A Distribution ShLA2+", 0)
        util.initmat(eb, "mf271", "g420", "P-A Distribution ShMA0", 0)
        util.initmat(eb, "mf272", "g421", "P-A Distribution ShMA1", 0)
        util.initmat(eb, "mf273", "g422", "P-A Distribution ShMA2+", 0)
        util.initmat(eb, "mf274", "g430", "P-A Distribution ShHA0", 0)
        util.initmat(eb, "mf275", "g431", "P-A Distribution ShHA1", 0)
        util.initmat(eb, "mf276", "g432", "P-A Distribution ShHA2+", 0)
        util.initmat(eb, "mf277", "g510", "P-A Distribution PBLA0", 0)
        util.initmat(eb, "mf278", "g511", "P-A Distribution PBLA1", 0)
        util.initmat(eb, "mf279", "g512", "P-A Distribution PBLA2+", 0)
        util.initmat(eb, "mf280", "g520", "P-A Distribution PBMA0", 0)
        util.initmat(eb, "mf281", "g521", "P-A Distribution PBMA1", 0)
        util.initmat(eb, "mf282", "g522", "P-A Distribution PBMA2+", 0)
        util.initmat(eb, "mf283", "g530", "P-A Distribution PBHA0", 0)
        util.initmat(eb, "mf284", "g531", "P-A Distribution PBHA1", 0)
        util.initmat(eb, "mf285", "g532", "P-A Distribution PBHA2+", 0)
        util.initmat(eb, "mf286", "g610", "P-A Distribution SoLA0", 0)
        util.initmat(eb, "mf287", "g611", "P-A Distribution SoLA1", 0)
        util.initmat(eb, "mf288", "g612", "P-A Distribution SoLA2+", 0)
        util.initmat(eb, "mf289", "g620", "P-A Distribution SoMA0", 0)
        util.initmat(eb, "mf290", "g621", "P-A Distribution SoMA1", 0)
        util.initmat(eb, "mf291", "g622", "P-A Distribution SoMA2+", 0)
        util.initmat(eb, "mf292", "g630", "P-A Distribution SoHA0", 0)
        util.initmat(eb, "mf293", "g631", "P-A Distribution SoHA1", 0)
        util.initmat(eb, "mf294", "g632", "P-A Distribution SoHA2+", 0)
        util.initmat(eb, "mf295", "g710", "P-A Distribution EcLA0", 0)
        util.initmat(eb, "mf296", "g711", "P-A Distribution EcLA1", 0)
        util.initmat(eb, "mf297", "g712", "P-A Distribution EcLA2+", 0)
        util.initmat(eb, "mf298", "g720", "P-A Distribution EcMA0", 0)
        util.initmat(eb, "mf299", "g721", "P-A Distribution EcMA1", 0)
        util.initmat(eb, "mf300", "g722", "P-A Distribution EcMA2+", 0)
        util.initmat(eb, "mf301", "g730", "P-A Distribution EcHA0", 0)
        util.initmat(eb, "mf302", "g731", "P-A Distribution EcHA1", 0)
        util.initmat(eb, "mf303", "g732", "P-A Distribution EcHA2+", 0)
        util.initmat(eb, "mf304", "g820", "P-A Distribution NwMA0", 0)
        util.initmat(eb, "mf305", "g821", "P-A Distribution NwMA1", 0)
        util.initmat(eb, "mf306", "g822", "P-A Distribution NwMA2+", 0)
        util.initmat(eb, "mf307", "g920", "P-A Distribution NoMA0", 0)
        util.initmat(eb, "mf308", "g921", "P-A Distribution NoMA1", 0)
        util.initmat(eb, "mf309", "g922", "P-A Distribution NoMA2+", 0)
        util.initmat(eb, "mf310", "z110", "O-D Distribution WkLA0", 0)
        util.initmat(eb, "mf311", "z111", "O-D Distribution WkLA1", 0)
        util.initmat(eb, "mf312", "z112", "O-D Distribution WkLA2+", 0)
        util.initmat(eb, "mf313", "z120", "O-D Distribution WkMA0", 0)
        util.initmat(eb, "mf314", "z121", "O-D Distribution WkMA1", 0)
        util.initmat(eb, "mf315", "z122", "O-D Distribution WkMA2+", 0)
        util.initmat(eb, "mf316", "z130", "O-D Distribution WkHA0", 0)
        util.initmat(eb, "mf317", "z131", "O-D Distribution WkHA1", 0)
        util.initmat(eb, "mf318", "z132", "O-D Distribution WkHA2+", 0)
        util.initmat(eb, "mf319", "z210", "O-D Distribution UvLA0", 0)
        util.initmat(eb, "mf320", "z211", "O-D Distribution UvLA1", 0)
        util.initmat(eb, "mf321", "z212", "O-D Distribution UvLA2+", 0)
        util.initmat(eb, "mf322", "z220", "O-D Distribution UvMA0", 0)
        util.initmat(eb, "mf323", "z221", "O-D Distribution UvMA1", 0)
        util.initmat(eb, "mf324", "z222", "O-D Distribution UvMA2+", 0)
        util.initmat(eb, "mf325", "z230", "O-D Distribution UvHA0", 0)
        util.initmat(eb, "mf326", "z231", "O-D Distribution UvHA1", 0)
        util.initmat(eb, "mf327", "z232", "O-D Distribution UvHA2+", 0)
        util.initmat(eb, "mf328", "z310", "O-D Distribution ScLA0", 0)
        util.initmat(eb, "mf329", "z311", "O-D Distribution ScLA1", 0)
        util.initmat(eb, "mf330", "z312", "O-D Distribution ScLA2+", 0)
        util.initmat(eb, "mf331", "z320", "O-D Distribution ScMA0", 0)
        util.initmat(eb, "mf332", "z321", "O-D Distribution ScMA1", 0)
        util.initmat(eb, "mf333", "z322", "O-D Distribution ScMA2+", 0)
        util.initmat(eb, "mf334", "z330", "O-D Distribution ScHA0", 0)
        util.initmat(eb, "mf335", "z331", "O-D Distribution ScHA1", 0)
        util.initmat(eb, "mf336", "z332", "O-D Distribution ScHA2+", 0)
        util.initmat(eb, "mf337", "z410", "O-D Distribution ShLA0", 0)
        util.initmat(eb, "mf338", "z411", "O-D Distribution ShLA1", 0)
        util.initmat(eb, "mf339", "z412", "O-D Distribution ShLA2+", 0)
        util.initmat(eb, "mf340", "z420", "O-D Distribution ShMA0", 0)
        util.initmat(eb, "mf341", "z421", "O-D Distribution ShMA1", 0)
        util.initmat(eb, "mf342", "z422", "O-D Distribution ShMA2+", 0)
        util.initmat(eb, "mf343", "z430", "O-D Distribution ShHA0", 0)
        util.initmat(eb, "mf344", "z431", "O-D Distribution ShHA1", 0)
        util.initmat(eb, "mf345", "z432", "O-D Distribution ShHA2+", 0)
        util.initmat(eb, "mf346", "z510", "O-D Distribution PBLA0", 0)
        util.initmat(eb, "mf347", "z511", "O-D Distribution PBLA1", 0)
        util.initmat(eb, "mf348", "z512", "O-D Distribution PBLA2+", 0)
        util.initmat(eb, "mf349", "z520", "O-D Distribution PBMA0", 0)
        util.initmat(eb, "mf350", "z521", "O-D Distribution PBMA1", 0)
        util.initmat(eb, "mf351", "z522", "O-D Distribution PBMA2+", 0)
        util.initmat(eb, "mf352", "z530", "O-D Distribution PBHA0", 0)
        util.initmat(eb, "mf353", "z531", "O-D Distribution PBHA1", 0)
        util.initmat(eb, "mf354", "z532", "O-D Distribution PBHA2+", 0)
        util.initmat(eb, "mf355", "z610", "O-D Distribution SoLA0", 0)
        util.initmat(eb, "mf356", "z611", "O-D Distribution SoLA1", 0)
        util.initmat(eb, "mf357", "z612", "O-D Distribution SoLA2+", 0)
        util.initmat(eb, "mf358", "z620", "O-D Distribution SoMA0", 0)
        util.initmat(eb, "mf359", "z621", "O-D Distribution SoMA1", 0)
        util.initmat(eb, "mf360", "z622", "O-D Distribution SoMA2+", 0)
        util.initmat(eb, "mf361", "z630", "O-D Distribution SoHA0", 0)
        util.initmat(eb, "mf362", "z631", "O-D Distribution SoHA1", 0)
        util.initmat(eb, "mf363", "z632", "O-D Distribution SoHA2+", 0)
        util.initmat(eb, "mf364", "z710", "O-D Distribution EcLA0", 0)
        util.initmat(eb, "mf365", "z711", "O-D Distribution EcLA1", 0)
        util.initmat(eb, "mf366", "z712", "O-D Distribution EcLA2+", 0)
        util.initmat(eb, "mf367", "z720", "O-D Distribution EcMA0", 0)
        util.initmat(eb, "mf368", "z721", "O-D Distribution EcMA1", 0)
        util.initmat(eb, "mf369", "z722", "O-D Distribution EcMA2+", 0)
        util.initmat(eb, "mf370", "z730", "O-D Distribution EcHA0", 0)
        util.initmat(eb, "mf371", "z731", "O-D Distribution EcHA1", 0)
        util.initmat(eb, "mf372", "z732", "O-D Distribution EcHA2+", 0)
        util.initmat(eb, "mo927", "Scr1", "Scratch_MO_1", 0)
        util.initmat(eb, "mo928", "Scr2", "Scratch_MO_2", 0)
        util.initmat(eb, "mo929", "Scr3", "Scratch_MO_3", 0)
        util.initmat(eb, "mo930", "Scr4", "Scratch_MO_4", 0)
        util.initmat(eb, "mf100", "kAuDsA", "Final Skim AutoDistanceAM", 0)
        util.initmat(eb, "mf101", "kAuTmA", "Final Skim AutoTimeAM", 0)
        util.initmat(eb, "mf102", "kAuTlA", "Final Skim AutoTollAM", 0)
        util.initmat(eb, "mf103", "kAuDsM", "Final Skim AutoDistanceMD", 0)
        util.initmat(eb, "mf104", "kAuTmM", "Final Skim AutoTimeMD", 0)
        util.initmat(eb, "mf105", "kAuTlM", "Final Skim AutoTollMD", 0)
        util.initmat(eb, "mf106", "kBsWtA", "Final Skim BusTotalWaitAM", 0)
        util.initmat(eb, "mf107", "kBsIvA", "Final Skim BusIVTTAM", 0)
        util.initmat(eb, "mf108", "kBsBrA", "Final Skim BusAvgBoardAM", 0)
        util.initmat(eb, "mf109", "kBsAxA", "Final Skim BusAuxAM", 0)
        util.initmat(eb, "mf110", "kBsFlA", "Final Skim BusFlagAM", 0)
        util.initmat(eb, "mf111", "kBsWtM", "Final Skim BusTotalWaitMD", 0)
        util.initmat(eb, "mf112", "kBsIvM", "Final Skim BusIVTTMD", 0)
        util.initmat(eb, "mf113", "kBsBrM", "Final Skim BusAvgBoardMD", 0)
        util.initmat(eb, "mf114", "kBsAxM", "Final Skim BusAuxMD", 0)
        util.initmat(eb, "mf115", "kBsFlM", "Final Skim BusFlagMD", 0)
        util.initmat(eb, "mf116", "kRBIvA", "Final Skim RailBusIVTTAM", 0)
        util.initmat(eb, "mf117", "kRRIvA", "Final Skim RailRailIVTTAM", 0)
        util.initmat(eb, "mf118", "kRlWtA", "Final Skim RailTotalWaitAM", 0)
        util.initmat(eb, "mf119", "kRlBrA", "Final Skim RailAvgBoardAM", 0)
        util.initmat(eb, "mf120", "kRlAxA", "Final Skim RailAuxAM", 0)
        util.initmat(eb, "mf121", "kRlFlA", "Final Skim RailFlagAM", 0)
        util.initmat(eb, "mf122", "kRAFlA", "Final Skim AuxFlagAM", 0)
        util.initmat(eb, "mf123", "kTRFlA", "Final Skim TotalRlTimeFlagAM", 0)
        util.initmat(eb, "mf124", "kRBIvM", "Final Skim RailBusIVTTMD", 0)
        util.initmat(eb, "mf125", "kRRIvM", "Final Skim RailRailIVTTMD", 0)
        util.initmat(eb, "mf126", "kRlWtM", "Final Skim RailTotalWaitMD", 0)
        util.initmat(eb, "mf127", "kRlBrM", "Final Skim RailAvgBoardMD", 0)
        util.initmat(eb, "mf128", "kRlAxM", "Final Skim RailAuxMD", 0)
        util.initmat(eb, "mf129", "kRlFlM", "Final Skim RailFlagMD", 0)
        util.initmat(eb, "mf130", "kRAFlM", "Final Skim AuxFlagMD", 0)
        util.initmat(eb, "mf131", "kTRFlM", "Final Skim TotalRlTimeFlagMD", 0)
        util.initmat(eb, "mf132", "kBsFtA", "Final Skim BusFilterAM", 0)
        util.initmat(eb, "mf133", "kBsFtM", "Final Skim BusFilterMD", 0)
        util.initmat(eb, "mf134", "kRlFtA", "Final Skim RailFilterAM", 0)
        util.initmat(eb, "mf135", "kRlFtM", "Final Skim RailFilterMD", 0)
        util.initmat(eb, "mf136", "kBsTrA", "Final Skim BusAvgTransferAM", 0)
        util.initmat(eb, "mf137", "kBsTrM", "Final Skim BusAvgTransferMD", 0)
        util.initmat(eb, "mf138", "kRlTrA", "Final Skim RailAvgTransferAM", 0)
        util.initmat(eb, "mf139", "kRlTrM", "Final Skim RailAvgTransferMD", 0)
        util.initmat(eb, "mf140", "kFcBsA", "Final Skim AMFactBus", 0)
        util.initmat(eb, "mf141", "kFcBsM", "Final Skim MDFactBus", 0)
        util.initmat(eb, "mf142", "kFcRlA", "Final Skim AMFactRail", 0)
        util.initmat(eb, "mf143", "kFcRlM", "Final Skim MDFactRail", 0)
        util.initmat(eb, "mf144", "kAuDsG", "Final Skim AvgAutoDistance", 0)
        util.initmat(eb, "mf145", "kAuTmG", "Final Skim AvgAutoTime", 0)
        util.initmat(eb, "mf146", "kAuTlG", "Final Skim AvgAutoTl", 0)
        util.initmat(eb, "mf147", "kBsWtG", "Final Skim AvgBusTotalWait", 0)
        util.initmat(eb, "mf148", "kBsIvG", "Final Skim AvgBusIVTT", 0)
        util.initmat(eb, "mf149", "kBsTrG", "Final Skim AvgBusTransfer", 0)
        util.initmat(eb, "mf150", "kBsAxG", "Final Skim AvgBusAux", 0)
        util.initmat(eb, "mf151", "kBsFtG", "Final Skim BusFilter", 0)
        util.initmat(eb, "mf152", "kRBIvG", "Final Skim AvgRailBusIVTT", 0)
        util.initmat(eb, "mf153", "kRRIvG", "Final Skim AvgRailRailIVTT", 0)
        util.initmat(eb, "mf154", "kRlWtG", "Final Skim AvgRailTotalWait", 0)
        util.initmat(eb, "mf155", "kRlTrG", "Final Skim AvgRailTransfer", 0)
        util.initmat(eb, "mf156", "kRlAxG", "Final Skim AvgRailAux", 0)
        util.initmat(eb, "mf157", "kRlFtG", "Final Skim AvgRailFilter", 0)
        util.initmat(eb, "mf158", "kWaFtG", "Final Skim AvgWalkFilter", 0)
        util.initmat(eb, "mf159", "kBkFtT", "Final Skim AvgBikeFilter", 0)
        util.initmat(eb, "mf162", "kSB", "Final SkimSchooBus", 0)
        util.initmat(eb, "mf163", "kTrOvA", "Final Skim TransitOVTTAM", 0)
        util.initmat(eb, "mf164", "kTrIvA", "Final Skim TransitIVTTAM", 0)
        util.initmat(eb, "mf167", "kTrOvM", "Final Skim TransitOVTTMD", 0)
        util.initmat(eb, "mf168", "kTrIvM", "Final Skim TransitIVTTMD", 0)
        util.initmat(eb, "mf925", "Scr1", "Scratch1", 0)
        util.initmat(eb, "mf926", "Scr2", "Scratch2", 0)
        util.initmat(eb, "mf927", "Scr3", "Scratch3", 0)
        ### Initialize peak hour demand matrices here in order to run assignment to generate starter skims
        util.initmat(eb, "mf843", "f1115v", "f1115v", 0)
        util.initmat(eb, "mf844", "f1215v", "f1215v", 0)
        util.initmat(eb, "mf845", "f1315v", "f1315v", 0)
        util.initmat(eb, "mf846", "f2115v", "f2115v", 0)
        util.initmat(eb, "mf847", "f2415v", "f2415v", 0)
        util.initmat(eb, "mf848", "f1125v", "f1125v", 0)
        util.initmat(eb, "mf849", "f1225v", "f1225v", 0)
        util.initmat(eb, "mf850", "f1325v", "f1325v", 0)
        util.initmat(eb, "mf851", "f2125v", "f2125v", 0)
        util.initmat(eb, "mf852", "f2425v", "f2425v", 0)
        util.initmat(eb, "mf853", "f3545b", "f3545b", 0.0000001)
        util.initmat(eb, "mf854", "f3555r", "f3555r", 0.0000001)
        util.initmat(eb, "mf980", "LgAM", "Veh-AMPH-unadjusted-LGV", 0)
        util.initmat(eb, "mf981", "HgAM", "Veh-AMPH-unadjusted-HGV", 0)
        util.initmat(eb, "mf856", "f1116v", "f1116v", 0)
        util.initmat(eb, "mf857", "f1216v", "f1216v", 0)
        util.initmat(eb, "mf858", "f1316v", "f1316v", 0)
        util.initmat(eb, "mf859", "f2116v", "f2116v", 0)
        util.initmat(eb, "mf860", "f2416v", "f2416v", 0)
        util.initmat(eb, "mf861", "f1126v", "f1126v", 0)
        util.initmat(eb, "mf862", "f1226v", "f1226v", 0)
        util.initmat(eb, "mf863", "f1326v", "f1326v", 0)
        util.initmat(eb, "mf864", "f2126v", "f2126v", 0)
        util.initmat(eb, "mf865", "f2426v", "f2426v", 0)
        util.initmat(eb, "mf866", "f3546b", "f3546b", 0.0000001)
        util.initmat(eb, "mf867", "f3556r", "f3556r", 0.0000001)
        util.initmat(eb, "mf982", "LgMD", "Veh-MDPH-unadjusted-LGV", 0)
        util.initmat(eb, "mf983", "HgMD", "Veh-MDPH-unadjusted-HGV", 0)

        util.initmat(eb, "ms160", "RlDeIn", "Initial Rail Demand for JLA", 0.0000001)

        # Batch in starter auto demand used for generating starter skims, demand is aggregated into 4 classes, SOV, HOV, Light Tr, Heavy Tr
        matrix_txn = _m.Modeller().tool("inro.emme.data.matrix.matrix_transaction")
        demand_file_AM = os.path.join(os.path.dirname(eb.path), "00_RUNMODEL", "AM_Starter_Demand.txt")
        demand_file_MD = os.path.join(os.path.dirname(eb.path), "00_RUNMODEL", "MD_Starter_Demand.txt")
        matrix_txn(transaction_file=demand_file_AM, throw_on_error=True)
        matrix_txn(transaction_file=demand_file_MD, throw_on_error=True)
