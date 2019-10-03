##---------------------------------------------------------------------
##--TransLink Phase 3.3 Regional Transportation Model
##--
##--Path: translink.RTM3.checking.UpdateTextFileVDF
##--Purpose: Update Base Network Text Files to the RTM3.3 VDFs
##---------------------------------------------------------------------
import inro.modeller as _m
import inro.emme.database as _d
import traceback as _traceback
import pandas as pd
import numpy as np
import os

class UpdateBaseNetworkVDF(_m.Tool()):
    scenarioList = _m.Attribute(str)
    scenarioInc = _m.Attribute(int)
    capacitydefinition = _m.Attribute(str)
    tool_run_msg = _m.Attribute(unicode)

    def __init__(self):
        self.scenarioInc = 0

    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Update Network VDF (Text File)"
        pb.description = "<object align='left'>Convert RTM3.2 Network to RTM3.3 Network: Update VDF </object><br>" \
                         "<object align='left'>RTM3.2 VDF: 1, 3-7, 25-88 </object><br>"\
                         "<object align='left'>RTM3.3 VDF: 11-16</object>"
        pb.branding_text = "TransLink"

        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)

        pb.add_text_box(tool_attribute_name="scenarioList",
                        size="50",
                        title="List of scenarios:",
                        note="separate by ;")
        pb.add_text_box(tool_attribute_name="scenarioInc",
                        size="5",
                        title="Increment Updated Scenario ID by:",
                        note="Replace selected scenarios if increment = 0")

        return pb.render()

    def run(self):
        self.tool_run_msg = ""
        try:
            eb = _m.Modeller().emmebank

            self(self.scenarioList, self.scenarioInc)
            self.tool_run_msg = _m.PageBuilder.format_info("Tool complete")
        except Exception, e:
            self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc(e))

    def __call__(self, scenarioList, scenarioInc, capacitydefinition="Nominal"):
        util = _m.Modeller().tool("translink.util")
        scenarioList = scenarioList.split(";")
        
        project = _m.Modeller().desktop.project
        proj_path = os.path.dirname(project.path)
        
        # define capacity per lane per function class digit
        CapacityUnit = {"Nominal":200, "Absolute":250}[capacitydefinition]
        ConnectorCapacity = 2000
        
        #update link extra attribute file
        for scenario in scenarioList:
            data_path = os.path.join(proj_path, "BaseNetworks", "extra_links_%s.txt" % scenario)
            link_attribute_file = pd.read_csv(data_path, delim_whitespace=True)
            
            attribute_dict = [["@capacityam","@lanesam","@vdfam"],
                              ["@capacitymd","@lanesmd","@vdfmd"],
                              ["@capacitypm","@lanespm","@vdfpm"]]
            
            #lookup capacity attributes
            for capacity, lanes, vdf in attribute_dict:
                link_attribute_file[capacity] = ConnectorCapacity #set default capacity to 2000 (for connectors)
                IsMerge = (link_attribute_file[vdf]>=3)&(link_attribute_file[vdf]<=7)
                link_attribute_file[capacity] = np.where(IsMerge, CapacityUnit*link_attribute_file[vdf],link_attribute_file[capacity])
                IsControlledIntersection = (link_attribute_file[vdf]>=20)&(link_attribute_file[vdf]<80)
                link_attribute_file[capacity] = np.where(IsControlledIntersection, CapacityUnit*(link_attribute_file[vdf]-link_attribute_file[vdf].mod(10))/10,link_attribute_file[capacity])
                IsFreeFlow = (link_attribute_file[vdf]>=80)&(link_attribute_file[vdf]<90)
                link_attribute_file[capacity] = np.where(IsFreeFlow, CapacityUnit*8,link_attribute_file[capacity])
                
                
            #add signal delay if the attribute does not exist
            signal_delay_exists = "@signal_delay" in link_attribute_file.columns.values.tolist()
            if not(signal_delay_exists):
                link_attribute_file["@signal_delay"] = np.where(IsControlledIntersection, 0.25, 0)
                
            #lookup new vdf
            for vdf in ["@vdfam","@vdfmd","@vdfpm"]:
                link_attribute_file[vdf] = 11 #default to connector
                link_attribute_file[vdf] = np.where(link_attribute_file[vdf]==2,12,link_attribute_file[vdf])
                IsMerge = (link_attribute_file[vdf]>=3)&(link_attribute_file[vdf]<=7)
                link_attribute_file[vdf] = np.where(IsMerge,13,link_attribute_file[vdf])
                IsControlledIntersection = (link_attribute_file[vdf]>=20)&(link_attribute_file[vdf]<80)
                link_attribute_file[vdf] = np.where(IsControlledIntersection,14,link_attribute_file[vdf])
                IsFreeFlow = (link_attribute_file[vdf]>=80)&(link_attribute_file[vdf]<=85)
                link_attribute_file[vdf] = np.where(IsFreeFlow,15,link_attribute_file[vdf])
                link_attribute_file[vdf] = np.where(link_attribute_file[vdf]==88,16,link_attribute_file[vdf])
                
            #export to extra_links_xxxx.txt file
            output_scenario = int(scenario) + int(scenarioInc)
            data_outputpath = os.path.join(proj_path, "BaseNetworks", "extra_links_%d.txt" % output_scenario)
            link_attribute_file.to_csv(data_outputpath, sep=' ', index=False)
            
            if int(scenarioInc)!=0: #if scenario increment is not zero, copy other base network files
                original_cwd = os.getcwd()
                os.chdir(os.path.join(proj_path, "BaseNetworks"))
                for file_type in ["base_network","link_shape","turns","extra_nodes","extra_turns","transit_lines","extra_transit_lines"]:
                    command = "copy %s_%s.txt %s_%d.txt"%(file_type, scenario, file_type, output_scenario)
                    os.system(command)
                os.chdir(original_cwd)
                
            #import, export network to 1) fix file formatting and 2) update vdf attribute
            eb = _m.Modeller().emmebank
            export_network = _m.Modeller().tool("translink.RTM3.export_network")
            import_network = _m.Modeller().tool("translink.RTM3.importnet")
            
            #load scenario title from base_network_xxxx.txt file
            #copy files
            fp = open(os.path.join(proj_path, "BaseNetworks", "base_network_%s.txt" % scenario))
            for i, line in enumerate(fp):
                if i == 1:
                   title = line.split(":")[-1].strip()
                   break
            fp.close()
            
            #import then export network to fix formating issues
            import_network(eb, output_scenario, title)
            util.emme_link_calc(eb.scenario(output_scenario), "vdf", "11", sel_link="vdf=1")
            util.emme_link_calc(eb.scenario(output_scenario), "vdf", "12", sel_link="vdf=2")
            util.emme_link_calc(eb.scenario(output_scenario), "vdf", "13", sel_link="vdf=3,7")
            util.emme_link_calc(eb.scenario(output_scenario), "vdf", "14", sel_link="vdf=20,75")
            util.emme_link_calc(eb.scenario(output_scenario), "vdf", "15", sel_link="vdf=80,85")
            util.emme_link_calc(eb.scenario(output_scenario), "vdf", "16", sel_link="vdf=88")
            export_network.export(output_scenario)

