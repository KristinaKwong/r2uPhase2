##---------------------------------------------------------------------
##--General EMME Python Tool
##--Namespace: translink.RTM3Analytics.GeographicTagging
##--Purpose: Tag polygon attribute to EMME links
##---------------------------------------------------------------------
import inro.modeller as _m
import traceback as _traceback
import fiona
import shapely.geometry as geom
import os.path as path

class TagPolygonToLink(_m.Tool()):
    scenario = _m.Attribute(_m.InstanceType)
    linkattribute = _m.Attribute(_m.InstanceType)
    polygonfile = _m.Attribute(_m.InstanceType)
    polygonfield = _m.Attribute(_m.InstanceType)
    algorithm = _m.Attribute(_m.InstanceType)
    excludeconnector = _m.Attribute(bool)
    default = _m.Attribute(float)

    tool_run_msg = _m.Attribute(unicode)

    def __init__(self):
        self.default = 0
        self.excludeconnector = True
        self.polygonfile = path.abspath(path.join(__file__ , "..", "..", "..", "Media", "TAZ", "TAZ1700_Whole_m2.shp"))
        self.polygonfield = "tazRev3"
        self.algorithm = "by_length"

    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Tag Polygon Attribute to EMME Link"
        pb.description = "Selected attibute in polygon shapefile will be tagged to EMME Link"

        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)

        pb.add_select_scenario("scenario", title = "Select Scenario for EMME Link Tags: ")
        #pb.add_select_extra_attribute("linkattribute", title = "Select Link Attribute for EMME Link Tags: ")
        pb.add_text_box(tool_attribute_name = "linkattribute", size = 20, title = "Select Link Attribute for EMME Link Tags: ")
        pb.add_select_file(tool_attribute_name = "polygonfile", window_type = "file",file_filter="*.shp",title="Polygon Shapefile: ")
        pb.add_text_box(tool_attribute_name = "polygonfield", size = 10, title = "Enter the field name in polygon shapefile: ")
        pb.add_text_box(tool_attribute_name = "algorithm", size = 50, title = "Enter algorithm if there are multiple match: ",
                        note = "tag_max; tag_min; by_length; do_not_change; set_to_-1.0")
        pb.add_checkbox("excludeconnector", label="Exclude Centroid Connectors")
        pb.add_text_box(tool_attribute_name = "default",title = "Default value if no match: ")

        return pb.render()

    def run(self):
        self.tool_run_msg = ""
        try:
            #linkattributeName = self.linkattribute.name
            linkattributeName = self.linkattribute
            self(self.scenario, linkattributeName, self.polygonfile, self.polygonfield, self.algorithm, self.excludeconnector, self.default)
            self.tool_run_msg = _m.PageBuilder.format_info("Tool complete")
        except Exception, e:
            self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc(e))

    @_m.logbook_trace("Tag Polygon Attribute To Link")
    def __call__(self,scenario,linkattributeName,polygonfile,polygonfield,algorithm,excludeconnector,default):
        self.CheckAttribute(scenario, linkattributeName, default)
        
        import logging
        logger = logging.getLogger()
        logger.setLevel(logging.CRITICAL)
        
        emme_network = scenario.get_network()
        
        with fiona.open(polygonfile) as polygonshapefile:
            polygon_meta = polygonshapefile.meta
            
            for linki in emme_network.links():
            
                if excludeconnector:
                    if (int(linki.i_node.id)>99999) and (int(linki.j_node.id)>99999):
                        pass # regular link, continue tagging
                    else:
                        #print("%s: IsConnector"%linki.id)
                        continue #to next EMME link
                
                #convert emme link to line string object, note this is for TransLink's RTM specific projection
                linkishape = [(x*1000, y*1000) for (x,y) in linki.shape]
                line = geom.LineString(linkishape)
                
                #Check if the link has been tagged
                With_match = False
                
                #check if emme link is completely within a polygon (most cases)
                for polygonfeature in polygonshapefile:
                    if line.within(geom.shape(polygonfeature["geometry"])):
                        linki[linkattributeName] = polygonfeature["properties"][polygonfield]
                        With_match = True
                        #print(linki.id)
                        break #stop looking for right polygon match
                
                #Multiple matching algorithm: tag_max; tag_min; by_length; do_not_change; set_to_-1.0
                if not(With_match) and algorithm!="do_not_change":
                    PercentIntersect = {}
                    for polygonfeature in polygonshapefile:
                        intersection = (geom.shape(polygonfeature["geometry"])).intersection(line)
                        if not(intersection.is_empty):
                            PercentIntersect[polygonfeature["properties"][polygonfield]]=intersection.length
                    
                    if PercentIntersect=={}:
                        linki[linkattributeName] = default
                        #print("%s: no match"%linki.id)
                    elif algorithm=="tag_max":
                        linki[linkattributeName]=max(list(PercentIntersect.keys()))
                        #print("%s: tag_max"%linki.id)
                    elif algorithm=="tag_min":
                        linki[linkattributeName]=min(list(PercentIntersect.keys()))
                        #print("%s: tag_min"%linki.id)
                    elif algorithm=="by_length":
                        linki[linkattributeName]=max(PercentIntersect, key=PercentIntersect.get)
                        #print("%s: by_length"%linki.id)
                    elif algorithm=="set_to_-1.0":
                        linki[linkattributeName]=float(algorithm.split("_")[-1])
                        #print("%s: set to %.0f"%(linki.id,float(algorithm.split("_")[-1])))
                    else:
                        linki[linkattributeName]=default
                        #print("%s: no match"%linki.id)
        
        scenario.publish_network(emme_network)
        
        
    def CheckAttribute(self, scenario, linkattributeName, default):
        AttributeExist = scenario.extra_attribute(linkattributeName)
        if AttributeExist:
            pass
        else:
            create_attr = _m.Modeller().tool("inro.emme.data.extra_attribute.create_extra_attribute")
            create_attr("LINK", linkattributeName,"tag polygon attribute", default, True, scenario)
