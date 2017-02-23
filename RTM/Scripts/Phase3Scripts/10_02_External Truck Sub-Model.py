##---------------------------------------------------------------------
##--TransLink Phase 2.2 Regional Transportation Model
##--
##--Path: translink.emme.stage5.step10.externaltruck
##--Purpose: This module generates external light and heavy truck matrices
##--         Regression functions are used to generate base and future demand
##--         Trip Distribution is conducted using 1999 Truck O-D survey
##---------------------------------------------------------------------
import inro.modeller as _m
import os

class ExternalTruckModel(_m.Tool()):
    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "External Truck Trips Model"
        pb.description = "Generates base/future forecasts for external light and heavy trucks trips"
        pb.branding_text = "TransLink"
        pb.runnable = False

        return pb.render()

    @_m.logbook_trace("External Truck Trips Model")
    def __call__(self, eb, Year):
        # Call Modules of External Model
        self.CrossBorder(eb, Year) # Import Cascade Cross-Border Matrices
        self.TripGeneration(Year)
        self.TripDistribution()
        self.TimeSlicing()

    @_m.logbook_trace("Import Cascade Cross-Border Matrices")
    def CrossBorder(self, eb, Year):
        util = _m.Modeller().tool("translink.util")

        util.initmat(eb, "mo1003",  "IRAdj", "IR Adjustment Calc", 0)
        util.initmat(eb, "md203",   "IRAdj", "IR Adjustment Calc", 0)
        util.initmat(eb, "mf1010", "IRLg24", "IR LgTruck Daily Trips", 0)
        util.initmat(eb, "mf1011", "IRHv24", "IR HvTruck Daily Trips", 0)
        util.initmat(eb, "mf1012", "IRLgAM", "IR LgTruck AM Trips", 0)
        util.initmat(eb, "mf1013", "IRHvAM", "IR HvTruck AM Trips", 0)
        util.initmat(eb, "mf1014", "IRLgMD", "IR LgTruck MD Trips", 0)
        util.initmat(eb, "mf1015", "IRHvMD", "IR HvTruck MD Trips", 0)

    @_m.logbook_trace("Time Slicing")
    def TimeSlicing(self):
        util = _m.Modeller().tool("translink.util")
        ## Time Slice 24 hour demands to AM and MD peak hour volumes
        # Inputs: mf184, mf185, Time Slice Factors from Screenline volumes
        # Outputs: Light AM, Light MD, Heavy AM, Heavy MD - mf186, mf188, mf187, mf189

# IB                 Light Trucks AM            Light Trucks MD               Heavy Trucks AM         Heavy Trucks MD
        FactorIB=[[0.05868,0.04086,0.05086],[0.05868,0.09194,0.10426],[0.03811,0.09500,0.02912],[0.07470,0.09866,0.11649]]

# OB                 Light Trucks AM            Light Trucks MD               Heavy Trucks AM         Heavy Trucks MD
        FactorOB=[[0.03613,0.02054,0.11882],[0.04517,0.1027,0.07505], [0.04328,0.05253,0.10976],[0.08743,0.10507,0.08537]]


        ConstraintList=[[1,2],[8,10],[11]]

                    ## LightAM, LightMD,HeavyAM, HeavyMD
        Matrix_List = ["mf1012","mf1014","mf1013","mf1015"]
        TripDistList= ["mf1010", "mf1011"]

        for i in range (len(TripDistList)) :
            for j in range (int((len(FactorIB)/2))):
                for k in range (len(FactorIB[j])):
                    spec = util.matrix_spec("", TripDistList[i]+"*"+str(FactorIB[2*i+j][k]))
                    for l in range (0, len(ConstraintList[k])):
                        spec["result"] = Matrix_List[2*i+j]
                        spec["constraint"]["by_zone"] = {"origins": str(ConstraintList[k][l]), "destinations": "*"}
                        util.compute_matrix(spec)

        for i in range (len(TripDistList)) :
            for j in range (int((len(FactorIB)/2))):
                for k in range (len(FactorOB[j])):
                    spec = util.matrix_spec("", str(TripDistList[i])+"*"+str(FactorOB[2*i+j][k]))
                    for l in range (0, len(ConstraintList[k])):
                        spec["result"] = Matrix_List[2*i+j]
                        spec["constraint"]["by_zone"] = {"origins": "*", "destinations": str(ConstraintList[k][l])}
                        util.compute_matrix(spec)
