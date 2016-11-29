##---------------------------------------------------------------------
##--TransLink Phase 3.0 Regional Transportation Model
##--
##--Path: translink.emme.xxxx
##--Purpose:
##---------------------------------------------------------------------
import inro.modeller as _m
import csv
import os
import numpy as np
import pandas as pd
import traceback as _traceback

class HbWork(_m.Tool()):

    ##Global attribute for Tool Run Message (successful/not successful)
    tool_run_msg = _m.Attribute(unicode)

    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Home Base Work"
        pb.description = "Calculate home base work person trips by mode and time of day"
        pb.branding_text = "TransLink"
        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)

        return pb.render()

    def run(self):
        self.tool_run_msg = ""
        try:
            self.__call__(_m.Modeller().emmebank)
            self.tool_run_msg = _m.PageBuilder.format_info("Tool complete")
        except Exception, e:
            self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc(e))

    @_m.logbook_trace("Run Home Base Work")
    def __call__(self, eb):

        util = _m.Modeller().tool("translink.emme.util")
        MChM = _m.Modeller().tool("translink.emme.modechoicemethods")
        input_path = util.get_input_path(eb)
#        self.matrix_batchins(eb)
        NoTAZ = len(util.get_matrix_numpy(eb, "mo51"))
        DistConv = 0.1

        Path = "U:/Projects/Development/Phase 3/TripDistribution/Targets/TripLengths/"
        PurpName = "hbw"
        Loc = os.path.join(Path, PurpName) + "_tl.csv"
        df = pd.DataFrame(pd.read_csv(Loc, sep = ","))

       ##############################################################################
        ##       Trip Distribution Calibration
       ##############################################################################

        Logsum =  [
                  "mf9000", "mf9001", "mf9002",
                  "mf9003", "mf9004", "mf9005",
                  "mf9006", "mf9007", "mf9008"
                   ]

        imp_list = [
                  "mf9500", "mf9501", "mf9502",
                  "mf9503", "mf9504", "mf9505",
                  "mf9506", "mf9507", "mf9508"
                   ]

        mo_list =  [
                    "mo161", "mo164", "mo167",
                    "mo162", "mo165", "mo168",
                    "mo163", "mo166", "mo169"
                   ]

        md_list =  ["md200"]

        out_list = [
                    "mf9510", "mf9511", "mf9512",
                    "mf9513", "mf9514", "mf9515",
                    "mf9516", "mf9517", "mf9518"
                   ]

        Distance = util.get_matrix_numpy(eb, 'mf8001')
        Distance_flat = Distance.flatten()


        LogSumInit =  0.3
        LambdaInit = -0.4
        AlphaInit  =  0.01
        GammaInit  = -0.0006
        NoSeg = len(mo_list)
        ObsDist = 14.17

        LambdaList = np.full(NoSeg, LambdaInit)
        AlphaList  = np.full(NoSeg, AlphaInit)
        GammaList = np.full(NoSeg, GammaInit)

        df['Lambda']       = LambdaList
        df['Alpha']        = AlphaList
        df['Gamma']        = GammaList
        AvgDistMod         = np.empty(NoSeg)
        AvgDistModSq       = np.empty(NoSeg)
        AvgDistModCu       = np.empty(NoSeg)


        # Iterate based on type

        LambdaRun = 1
        AlphaRun  = 2
        GammaRun  = 3

        RunType = GammaRun

        counter = 1

        while counter > 0:

            counter += 1
            Cycle = counter - 1

            for iteration in range (1, RunType + 1):

                MChM.ImpCalc(eb, Logsum, imp_list, LogSumInit, df['Lambda'] , df['Alpha'], df['Gamma'], Distance, RunType)
                MChM.two_dim_matrix_balancing(eb, mo_list, md_list, imp_list, out_list, 60)
                AvgDistTot , MaxValue, df = MChM.Check_Convergence(eb, NoSeg, out_list, Distance_flat,
                                            AvgDistMod, AvgDistModSq, AvgDistModCu, df, RunType)

                if MaxValue < DistConv:
                    counter = 0
                    df.to_csv("F:/Scratch/Out1"+str(Cycle)+".csv")
                    break

                if iteration == 0:

                    LogSumInit = LogSumInit*AvgDistTot/ObsDist
                    print ("Logsum,", LogSumInit)
                    df.to_csv("F:/Scratch/Out0"+str(Cycle)+".csv")

                if iteration == 1:

                    df['Lambda'] = df['Lambda']*df['AvgDistMod']/df['avgTL']
                    df.to_csv("F:/Scratch/Out1"+str(Cycle)+".csv")

                if iteration == 2:

                    df['Alpha'] = df['Alpha']*df['AvgDistModSq']/df['avgTLsqd']
                    df.to_csv("F:/Scratch/Out2"+str(Cycle)+".csv")

                if iteration == 3:

                    df['Gamma'] = df['Gamma']*df['AvgDistModCu']/df['avgTLcub']
                    df.to_csv("F:/Scratch/Out3"+str(Cycle)+".csv")




