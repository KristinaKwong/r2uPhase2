
# coding: utf-8

# ## Setup

# In[1]:

import inro.modeller as _m
import os


# In[2]:

emmebank_dir = os.path.dirname(_m.Modeller().emmebank.path)
userpath = os.path.expanduser('~')
output_path = userpath + '\\desktop\\skim'

if not os.path.exists(output_path):
    os.makedirs(output_path)


# In[3]:

def update_output_path(folder_name):
    emmebank_dir = os.path.dirname(_m.Modeller().emmebank.path)
    userpath = os.path.expanduser('~')
    output_path = userpath + '\\desktop\\{new_name}'.format(new_name=folder_name)

    if not os.path.exists(output_path):
        os.makedirs(output_path)
    return output_path


# In[4]:

export_matrix = _m.Modeller().tool('inro.emme.data.matrix.export_matrices')


# In[5]:

def batch_mat_exporter(mf_export_list, output_file_list, output_path):
    for i in range(0, len(mf_export_list)):
        current_mat = 'mf%d' % mf_export_list[i]
        ofile = '%s.txt' % output_file_list[i]
        output_file = os.path.join(output_path, ofile)
        export_matrix(matrices=current_mat,
                    export_file=output_file, 
                    field_separator='TAB',
                    export_format="PROMPT_DATA_FORMAT",
                    skip_default_values=False,
                    full_matrix_line_format="ONE_ENTRY_PER_LINE")


# ## Export Auto Skims

# In[79]:

auto_mf_export_list = [2030,2031,2032,2033,2034,2035,2036,2037,2038]


# In[80]:

auto_output_file_list = ['AutoDistanceAMWk','AutoTimeAMWk','AutoTollAMWk','AutoDistanceMDWk','AutoTimeMDWk','AutoTollMDWk','AutoDistancePMWk',
                    'AutoTimePMWk','AutoTollPMWk']


# In[81]:

output_path = update_output_path('auto')


# In[82]:

batch_mat_exporter(auto_mf_export_list, auto_output_file_list, output_path)


# In[83]:

auto_mf_export_list = [930,931,932,942,943,944,2000,2001,2002]


# In[84]:

auto_output_file_list = ['AutoDistanceAMNWk','AutoTimeAMNWk','AutoTollAMNWk','AutoDistanceMDNWk','AutoTimeMDNWk','AutoTollMDNWk','AutoDistancePMNWk',
                    'AutoTimePMNWk','AutoTollPMNWk']


# In[85]:

output_path = update_output_path('auto')


# In[86]:

batch_mat_exporter(auto_mf_export_list, auto_output_file_list, output_path)


# ## Export Bus Skims

# In[14]:

bus_mf_export_list = [106,107,108,109,110,111,112,113,114,115,2106,2107,2108,2109,2110]


# In[15]:

bus_output_file_list = ['BusTotalWaitAM','BusIVTTAM','BusAvgBoardAM','BusAuxAM','BusFlagAM','BusTotalWaitMD','BusIVTTMD',
                    'BusAvgBoardMD','BusAuxMD','BusFlagMD','BusTotalWaitPM','BusIVTTPM','BusAvgBoardPM','BusAuxPM','BusFlagPM']


# In[16]:

output_path = update_output_path('bus')


# In[17]:

batch_mat_exporter(bus_mf_export_list, bus_output_file_list, output_path)


# ## Export P2 Rail Skims (should not be used for development)

# In[18]:

rail_mf_export_list = [116,117,118,119,120,121,122,123,124,125,126,127,128,129,130,131,2116,2117,2118,2119,2120,2121,2122,2123]


# In[19]:

rail_output_file_list = ['RailBusIVTTAM','RailRailIVTTAM','RailTotalWaitAM','RailAvgBoardAM','RailAuxAM','RailFlagAM',
                         'AuxFlagAM','TotalRlTimeFlagAM','RailBusIVTTMD','RailRailIVTTMD','RailTotalWaitMD','RailAvgBoardMD',
                         'RailAuxMD','RailFlagMD','AuxFlagMD','TotalRlTimeFlagMD','RailBusIVTTPM','RailRailIVTTPM',
                         'RailTotalWaitPM','RailAvgBoardPM','RailAuxPM','RailFlagPM','AuxFlagPM','TotalRlTimeFlagPM']


# In[20]:

#batch_mat_exporter(rail_mf_export_list, rail_output_file_list, output_path)


# ## Export Other Transit Skims

# In[21]:

transit_mf_export_list = [160,161,163,164,167,168,2163,2164]


# In[22]:

transit_output_file_list = ['BusFare','RailFare','TransitOVTTAM','TransitIVTTAM','TransitOVTTMD',
                            'TransitIVTTMD','TransitOVTTPM','TransitIVTTPM']


# In[23]:

output_path = update_output_path('transit')


# In[24]:

batch_mat_exporter(transit_mf_export_list, transit_output_file_list, output_path)


# ## Export P3 Rail Skims

# In[25]:

p3_rail_mf_export_list = [5000,5001,5002,5003,5004,5005,5006,5007,5008,5009,5010,5011,5012,5013,5014]


# In[26]:

p3_rail_output_file_list = ['RailBusIVTTAM','RailRailIVTTAM','RailTotalWaitAM','RailAvgBoardAM','RailAuxAM',
                         'RailBusIVTTMD','RailRailIVTTMD','RailTotalWaitMD','RailAvgBoardMD','RailAuxMD',
                         'RailBusIVTTPM','RailRailIVTTPM','RailTotalWaitPM','RailAvgBoardPM','RailAuxPM']


# In[27]:

output_path = update_output_path('rail')


# In[28]:

batch_mat_exporter(p3_rail_mf_export_list, p3_rail_output_file_list, output_path)


# ## Export P3 WCE skims

# In[29]:

p3_wce_mf_export_list = [5050,5051,5052,5053,5054,5055,5056,5057,5058,5059,5060,5061,5062,5063,5064,5065,5066,5067]


# In[30]:

p3_wce_output_file_list = ['WCEBusIVTTAM','WCERailIVTTAM','WCEWCEIVTTAM','WCETotalWaitAM','WCEAvgBoardAM','WCEAuxAM',
                         'WCEBusIVTTMD','WCERailIVTTMD','WCEWCEIVTTMD','WCETotalWaitMD','WCEAvgBoardMD','WCEAuxMD',
                         'WCEBusIVTTPM','WCERailIVTTPM','WCEWCEIVTTPM','WCETotalWaitPM','WCEAvgBoardPM','WCEAuxPM']


# In[31]:

output_path = update_output_path('wce')


# In[32]:

batch_mat_exporter(p3_wce_mf_export_list, p3_wce_output_file_list, output_path)


# ## Export P3 Park and Ride Bus Skims PA Direction

# ####am work

# In[1]:

p3_prbus_mf_export_list = [6007, 6008, 6009, 6010, 6011, 6012, 6013, 6014]
p3_prbus_output_file_list = ['prBusautimeAMWk', 'prBusautollAMWk', 'prBusautdistAMWk', 'prBusbusIVTAMWk', 'prBusbusWtAMWk', 
                             'prBusbordsAMWk', 'prBusauxAMWk', 'prBusfareAMWk']
output_path = update_output_path('bus_pr_pa')
batch_mat_exporter(p3_prbus_mf_export_list, p3_prbus_output_file_list, output_path)        


# ####md work

# In[34]:

p3_prbus_mf_export_list = [6052, 6053, 6054, 6055, 6056, 6057, 6058, 6059]
p3_prbus_output_file_list = ['prBusautimeMDWk', 'prBusautollMDWk', 'prBusautdistMDWk', 'prBusbusIVTMDWk', 'prBusbusWtMDWk',
                             'prBusbordsMDWk', 'prBusauxMDWk', 'prBusfareMDWk']
batch_mat_exporter(p3_prbus_mf_export_list, p3_prbus_output_file_list, output_path)        


# ####pm work

# In[35]:

p3_prbus_mf_export_list = [6092, 6093, 6094, 6095, 6096, 6097, 6098, 6099] 
p3_prbus_output_file_list = ['prBusautimePMWk', 'prBusautollPMWk', 'prBusautdistPMWk', 'prBusbusIVTPMWk', 'prBusbusWtPMWk', 
                             'prBusbordsPMWk', 'prBusauxPMWk', 'prBusfarePMWk'] 
batch_mat_exporter(p3_prbus_mf_export_list, p3_prbus_output_file_list, output_path)         


# ####am nonwork

# In[36]:

p3_prbus_mf_export_list = [6137, 6138, 6139, 6140, 6141, 6142, 6143, 6144]
p3_prbus_output_file_list = ['prBusautimeAMNWk', 'prBusautollAMNWk', 'prBusautdistAMNWk', 'prBusbusIVTAMNWk', 'prBusbusWtAMNWk',
                             'prBusbordsAMNWk', 'prBusauxAMNWk', 'prBusfareAMNWk']
batch_mat_exporter(p3_prbus_mf_export_list, p3_prbus_output_file_list, output_path)        


# ####md nonwork

# In[37]:

p3_prbus_mf_export_list = [6177, 6178, 6179, 6180, 6181, 6182, 6183, 6184]
p3_prbus_output_file_list = ['prBusautimeMDNWk', 'prBusautollMDNWk', 'prBusautdistMDNWk', 'prBusbusIVTMDNWk', 'prBusbusWtMDNWk', 
                             'prBusbordsMDNWk', 'prBusauxMDNWk', 'prBusfareMDNWk']
batch_mat_exporter(p3_prbus_mf_export_list, p3_prbus_output_file_list, output_path)        


# ####pm nonwork

# In[38]:

p3_prbus_mf_export_list = [6217, 6218, 6219, 6220, 6221, 6222, 6223, 6224]
p3_prbus_output_file_list = ['prBusautimePMNWk', 'prBusautollPMNWk', 'prBusautdistPMNWk', 'prBusbusIVTPMNWk', 'prBusbusWtPMNWk', 
                             'prBusbordsPMNWk', 'prBusauxPMNWk', 'prBusfarePMNWk']
batch_mat_exporter(p3_prbus_mf_export_list, p3_prbus_output_file_list, output_path)        
        


# ##Export P3 Park and Ride Rail Skims

# ####am work

# In[39]:

p3_prrail_mf_export_list = [6017, 6018, 6019, 6020, 6021, 6022, 6023, 6024, 6025, 6026]
p3_prrail_output_file_list = ['prRailautimeAMWk', 'prRailautollAMWk', 'prRailautdistAMWk', 'prRailrailIVTAMWk', 'prRailrailWtAMWk',
                              'prRailbusIVTAMWk', 'prRailbusWtAMWk', 'prRailbordsAMWk', 'prRailauxAMWk', 'prRailfareAMWk']
output_path = update_output_path('rail_pr_pa')
batch_mat_exporter(p3_prrail_mf_export_list, p3_prrail_output_file_list, output_path)          


# ####md work

# In[40]:

p3_prrail_mf_export_list = [6062, 6063, 6064, 6065, 6066, 6067, 6068, 6069, 6070, 6071]
p3_prrail_output_file_list = ['prRailautimeMDWk', 'prRailautollMDWk', 'prRailautdistMDWk', 'prRailrailIVTMDWk', 'prRailrailWtMDWk',
                              'prRailbusIVTMDWk', 'prRailbusWtMDWk', 'prRailbordsMDWk', 'prRailauxMDWk', 'prRailfareMDWk']
batch_mat_exporter(p3_prrail_mf_export_list, p3_prrail_output_file_list, output_path)          


# ####pm work

# In[41]:

p3_prrail_mf_export_list = [6102, 6103, 6104, 6105, 6106, 6107, 6108, 6109, 6110, 6111]
p3_prrail_output_file_list = ['prRailautimePMWk', 'prRailautollPMWk', 'prRailautdistPMWk', 'prRailrailIVTPMWk', 'prRailrailWtPMWk',
                              'prRailbusIVTPMWk', 'prRailbusWtPMWk', 'prRailbordsPMWk', 'prRailauxPMWk', 'prRailfarePMWk']
batch_mat_exporter(p3_prrail_mf_export_list, p3_prrail_output_file_list, output_path)          


# ####am nonwork

# In[42]:

p3_prrail_mf_export_list = [6147, 6148, 6149, 6150, 6151, 6152, 6153, 6154, 6155, 6156]
p3_prrail_output_file_list = ['prRailautimeAMNWk', 'prRailautollAMNWk', 'prRailautdistAMNWk', 'prRailrailIVTAMNWk', 'prRailrailWtAMNWk',
                              'prRailbusIVTAMNWk', 'prRailbusWtAMNWk', 'prRailbordsAMNWk', 'prRailauxAMNWk', 'prRailfareAMNWk']
batch_mat_exporter(p3_prrail_mf_export_list, p3_prrail_output_file_list, output_path)          


# ####md nonwork

# In[43]:

p3_prrail_mf_export_list = [6187, 6188, 6189, 6190, 6191, 6192, 6193, 6194, 6195, 6196]
p3_prrail_output_file_list = ['prRailautimeMDNWk', 'prRailautollMDNWk', 'prRailautdistMDNWk', 'prRailrailIVTMDNWk', 'prRailrailWtMDNWk',
                              'prRailbusIVTMDNWk', 'prRailbusWtMDNWk', 'prRailbordsMDNWk', 'prRailauxMDNWk', 'prRailfareMDNWk']
batch_mat_exporter(p3_prrail_mf_export_list, p3_prrail_output_file_list, output_path)          


# ####pm nonwork

# In[44]:

p3_prrail_mf_export_list = [6227, 6228, 6229, 6230, 6231, 6232, 6233, 6234, 6235, 6236]
p3_prrail_output_file_list = ['prRailautimePMNWk', 'prRailautollPMNWk', 'prRailautdistPMNWk', 'prRailrailIVTPMNWk', 'prRailrailWtPMNWk',
                              'prRailbusIVTPMNWk', 'prRailbusWtPMNWk', 'prRailbordsPMNWk', 'prRailauxPMNWk', 'prRailfarePMNWk']
batch_mat_exporter(p3_prrail_mf_export_list, p3_prrail_output_file_list, output_path)          


# ##Export P3 Park and Ride WCE Skims

# ####am work

# In[45]:

p3_prwce_mf_export_list = [6032, 6033, 6034, 6035, 6036, 6037, 6038, 6039, 6040, 6041, 6042, 6043]
p3_prwce_output_file_list = ['prWCEautimeAMWk', 'prWCEautollAMWk', 'prWCEautdistAMWk', 'prWCEwceIVTAMWk', 'prWCEwceWtAMWk', 
                             'prWCErailIVTAMWk', 'prWCErailWtAMWk', 'prWCEbusIVTAMWk', 'prWCEbusWtAMWk', 'prWCEbordsAMWk',
                             'prWCEauxAMWk', 'prWCEfareAMWk']
output_path = update_output_path('wce_pr_pa')
batch_mat_exporter(p3_prwce_mf_export_list, p3_prwce_output_file_list, output_path)            
        



# ####pm work

# In[47]:

p3_prwce_mf_export_list = [6117, 6118, 6119, 6120, 6121, 6122, 6123, 6124, 6125, 6126, 6127, 6128]
p3_prwce_output_file_list = ['prWCEautimePMWk', 'prWCEautollPMWk', 'prWCEautdistPMWk', 'prWCEwceIVTPMWk', 'prWCEwceWtPMWk', 
                             'prWCErailIVTPMWk', 'prWCErailWtPMWk', 'prWCEbusIVTPMWk', 'prWCEbusWtPMWk', 'prWCEbordsPMWk', 
                             'prWCEauxPMWk', 'prWCEfarePMWk']
batch_mat_exporter(p3_prwce_mf_export_list, p3_prwce_output_file_list, output_path)            


# ####am nonwork

# In[48]:

p3_prwce_mf_export_list = [6162, 6163, 6164, 6165, 6166, 6167, 6168, 6169, 6170, 6171, 6172, 6173]
p3_prwce_output_file_list = ['prWCEautimeAMNWk', 'prWCEautollAMNWk', 'prWCEautdistAMNWk', 'prWCEwceIVTAMNWk', 'prWCEwceWtAMNWk',
                             'prWCErailIVTAMNWk', 'prWCErailWtAMNWk', 'prWCEbusIVTAMNWk', 'prWCEbusWtAMNWk', 'prWCEbordsAMNWk', 
                             'prWCEauxAMNWk', 'prWCEfareAMNWk']
batch_mat_exporter(p3_prwce_mf_export_list, p3_prwce_output_file_list, output_path)            


# ####pm nonwork

# In[50]:

p3_prwce_mf_export_list = [6242, 6243, 6244, 6245, 6246, 6247, 6248, 6249, 6250, 6251, 6252, 6253]
p3_prwce_output_file_list = ['prWCEautimePMNWk', 'prWCEautollPMNWk', 'prWCEautdistPMNWk', 'prWCEwceIVTPMNWk', 'prWCEwceWtPMNWk',
                             'prWCErailIVTPMNWk', 'prWCErailWtPMNWk', 'prWCEbusIVTPMNWk', 'prWCEbusWtPMNWk', 'prWCEbordsPMNWk', 
                             'prWCEauxPMNWk', 'prWCEfarePMNWk']
batch_mat_exporter(p3_prwce_mf_export_list, p3_prwce_output_file_list, output_path)            


# ##Export P3 Park and Ride Best Lot Choice

# ####work trips

# In[51]:

output_path = update_output_path('transit')


# PA Direction
p3__mf_export_list = [6000, 6001, 6002]
p3__output_file_list = ['prBuslotChceWkPA', 'prRaillotChceWkPA', 'prWCElotChceWkPA']
batch_mat_exporter(p3__mf_export_list, p3__output_file_list, output_path)   


# ####nonwork trips


p3__mf_export_list = [6130, 6131, 6132]
p3__output_file_list = ['prBuslotChceNWkPA', 'prRaillotChceNWkPA', 'prWCElotChceNWkPA']
batch_mat_exporter(p3__mf_export_list, p3__output_file_list, output_path)   


# ###AP direction
# work
p3__mf_export_list =[6300,6301,6302]
p3__output_file_list =['prBuslotChceWkAP','prRaillotChceWkAP','prWCElotChceWkAP']
batch_mat_exporter(p3__mf_export_list, p3__output_file_list, output_path)

# non work
p3__mf_export_list =[6430,6431,6432]
p3__output_file_list =['prBuslotChceNWkAP','prRaillotChceNWkAP','prWCElotChceNWkAP']
batch_mat_exporter(p3__mf_export_list, p3__output_file_list, output_path)



# #### New AP direction

# Bus

output_path = update_output_path('bus_pr_ap')

# work

p3_prbus_mf_export_list =[6307,6308,6309,6310,6311,6312,6313,6314]
p3_prbus_output_file_list =['prBusautimeAMWk','prBusautollAMWk','prBusautdistAMWk','prBusbusIVTAMWk','prBusbusWtAMWk','prBusbordsAMWk','prBusauxAMWk','prBusfareAMWk']
batch_mat_exporter(p3_prbus_mf_export_list, p3_prbus_output_file_list, output_path)


p3_prbus_mf_export_list =[6352,6353,6354,6355,6356,6357,6358,6359]
p3_prbus_output_file_list =['prBusautimeMDWk','prBusautollMDWk','prBusautdistMDWk','prBusbusIVTMDWk','prBusbusWtMDWk','prBusbordsMDWk','prBusauxMDWk','prBusfareMDWk']
batch_mat_exporter(p3_prbus_mf_export_list, p3_prbus_output_file_list, output_path)

p3_prbus_mf_export_list =[6392,6393,6394,6395,6396,6397,6398,6399]
p3_prbus_output_file_list =['prBusautimePMWk','prBusautollPMWk','prBusautdistPMWk','prBusbusIVTPMWk','prBusbusWtPMWk','prBusbordsPMWk','prBusauxPMWk','prBusfarePMWk']
batch_mat_exporter(p3_prbus_mf_export_list, p3_prbus_output_file_list, output_path)

# nonwork
p3_prbus_mf_export_list =[6437,6438,6439,6440,6441,6442,6443,6444]
p3_prbus_output_file_list =['prBusautimeAMNWk','prBusautollAMNWk','prBusautdistAMNWk','prBusbusIVTAMNWk','prBusbusWtAMNWk','prBusbordsAMNWk','prBusauxAMNWk','prBusfareAMNWk']
batch_mat_exporter(p3_prbus_mf_export_list, p3_prbus_output_file_list, output_path)


p3_prbus_mf_export_list =[6477,6478,6479,6480,6481,6482,6483,6484]
p3_prbus_output_file_list =['prBusautimeMDNWk','prBusautollMDNWk','prBusautdistMDNWk','prBusbusIVTMDNWk','prBusbusWtMDNWk','prBusbordsMDNWk','prBusauxMDNWk','prBusfareMDNWk']
batch_mat_exporter(p3_prbus_mf_export_list, p3_prbus_output_file_list, output_path)


p3_prbus_mf_export_list =[6517,6518,6519,6520,6521,6522,6523,6524]
p3_prbus_output_file_list =['prBusautimePMNWk','prBusautollPMNWk','prBusautdistPMNWk','prBusbusIVTPMNWk','prBusbusWtPMNWk','prBusbordsPMNWk','prBusauxPMNWk','prBusfarePMNWk']
batch_mat_exporter(p3_prbus_mf_export_list, p3_prbus_output_file_list, output_path)


# Rail

output_path = update_output_path('rail_pr_ap')

# work

p3_prrail_mf_export_list =[6317,6318,6319,6320,6321,6322,6323,6324,6325,6326]
p3_prrail_output_file_list =['prRailautimeAMWk','prRailautollAMWk','prRailautdistAMWk','prRailrailIVTAMWk','prRailrailWtAMWk','prRailbusIVTAMWk','prRailbusWtAMWk','prRailbordsAMWk','prRailauxAMWk','prRailfareAMWk']
batch_mat_exporter(p3_prrail_mf_export_list, p3_prrail_output_file_list, output_path)


p3_prrail_mf_export_list =[6362,6363,6364,6365,6366,6367,6368,6369,6370,6371]
p3_prrail_output_file_list =['prRailautimeMDWk','prRailautollMDWk','prRailautdistMDWk','prRailrailIVTMDWk','prRailrailWtMDWk','prRailbusIVTMDWk','prRailbusWtMDWk','prRailbordsMDWk','prRailauxMDWk','prRailfareMDWk']
batch_mat_exporter(p3_prrail_mf_export_list, p3_prrail_output_file_list, output_path)


p3_prrail_mf_export_list =[6402,6403,6404,6405,6406,6407,6408,6409,6410,6411]
p3_prrail_output_file_list =['prRailautimePMWk','prRailautollPMWk','prRailautdistPMWk','prRailrailIVTPMWk','prRailrailWtPMWk','prRailbusIVTPMWk','prRailbusWtPMWk','prRailbordsPMWk','prRailauxPMWk','prRailfarePMWk']
batch_mat_exporter(p3_prrail_mf_export_list, p3_prrail_output_file_list, output_path)


#nonwork

p3_prrail_mf_export_list =[6447,6448,6449,6450,6451,6452,6453,6454,6455,6456]
p3_prrail_output_file_list =['prRailautimeAMNWk','prRailautollAMNWk','prRailautdistAMNWk','prRailrailIVTAMNWk','prRailrailWtAMNWk','prRailbusIVTAMNWk','prRailbusWtAMNWk','prRailbordsAMNWk','prRailauxAMNWk','prRailfareAMNWk']
batch_mat_exporter(p3_prrail_mf_export_list, p3_prrail_output_file_list, output_path)


p3_prrail_mf_export_list =[6487,6488,6489,6490,6491,6492,6493,6494,6495,6496]
p3_prrail_output_file_list =['prRailautimeMDNWk','prRailautollMDNWk','prRailautdistMDNWk','prRailrailIVTMDNWk','prRailrailWtMDNWk','prRailbusIVTMDNWk','prRailbusWtMDNWk','prRailbordsMDNWk','prRailauxMDNWk','prRailfareMDNWk']
batch_mat_exporter(p3_prrail_mf_export_list, p3_prrail_output_file_list, output_path)


p3_prrail_mf_export_list =[6527,6528,6529,6530,6531,6532,6533,6534,6535,6536]
p3_prrail_output_file_list =['prRailautimePMNWk','prRailautollPMNWk','prRailautdistPMNWk','prRailrailIVTPMNWk','prRailrailWtPMNWk','prRailbusIVTPMNWk','prRailbusWtPMNWk','prRailbordsPMNWk','prRailauxPMNWk','prRailfarePMNWk']
batch_mat_exporter(p3_prrail_mf_export_list, p3_prrail_output_file_list, output_path)

# WCE


output_path = update_output_path('wce_pr_ap')

#Work

p3_prwce_mf_export_list =[6332,6333,6334,6335,6336,6337,6338,6339,6340,6341,6342,6343]
p3_prwce_output_file_list =['prWCEautimeAMWk','prWCEautollAMWk','prWCEautdistAMWk','prWCEwceIVTAMWk','prWCEwceWtAMWk','prWCErailIVTAMWk','prWCErailWtAMWk','prWCEbusIVTAMWk','prWCEbusWtAMWk','prWCEbordsAMWk','prWCEauxAMWk','prWCEfareAMWk']
batch_mat_exporter(p3_prwce_mf_export_list, p3_prwce_output_file_list, output_path)


p3_prwce_mf_export_list =[6417,6418,6419,6420,6421,6422,6423,6424,6425,6426,6427,6428]
p3_prwce_output_file_list =['prWCEautimePMWk','prWCEautollPMWk','prWCEautdistPMWk','prWCEwceIVTPMWk','prWCEwceWtPMWk','prWCErailIVTPMWk','prWCErailWtPMWk','prWCEbusIVTPMWk','prWCEbusWtPMWk','prWCEbordsPMWk','prWCEauxPMWk','prWCEfarePMWk']
batch_mat_exporter(p3_prwce_mf_export_list, p3_prwce_output_file_list, output_path)


# nonwork

p3_prwce_mf_export_list =[6462,6463,6464,6465,6466,6467,6468,6469,6470,6471,6472,6473]
p3_prwce_output_file_list =['prWCEautimeAMNWk','prWCEautollAMNWk','prWCEautdistAMNWk','prWCEwceIVTAMNWk','prWCEwceWtAMNWk','prWCErailIVTAMNWk','prWCErailWtAMNWk','prWCEbusIVTAMNWk','prWCEbusWtAMNWk','prWCEbordsAMNWk','prWCEauxAMNWk','prWCEfareAMNWk']
batch_mat_exporter(p3_prwce_mf_export_list, p3_prwce_output_file_list, output_path)


p3_prwce_mf_export_list =[6542,6543,6544,6545,6546,6547,6548,6549,6550,6551,6552,6553]
p3_prwce_output_file_list =['prWCEautimePMNWk','prWCEautollPMNWk','prWCEautdistPMNWk','prWCEwceIVTPMNWk','prWCEwceWtPMNWk','prWCErailIVTPMNWk','prWCErailWtPMNWk','prWCEbusIVTPMNWk','prWCEbusWtPMNWk','prWCEbordsPMNWk','prWCEauxPMNWk','prWCEfarePMNWk']
batch_mat_exporter(p3_prwce_mf_export_list, p3_prwce_output_file_list, output_path)






