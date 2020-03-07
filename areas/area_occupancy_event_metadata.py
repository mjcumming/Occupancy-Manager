'''

Area Occupancy Event Metadata

Interface to an Area item metadata

'''
 

import personal.item_metadata.metadata_item_namespace
reload (personal.item_metadata.metadata_item_namespace) 
from personal.item_metadata.metadata_item_namespace import Metadata_Item_Namespace


class Area_Occupancy_Event_Metadata(Metadata_Item_Namespace):

    def __init__ (self, item_name):
        Metadata_Item_Namespace.__init__(self, item_name, "OccupancySettings")

    def get_occupied_actions(self):
        s = self.get_value_for_configuration_key('OccupiedActions')
        if s:
            return str.split(s,',')
        else:
            return []


    def get_vacant_actions(self):
        s = self.get_value_for_configuration_key('VacantActions')
        if s:
            return str.split(s,',')
        else:
            return []

    def get_occupancy_time(self):
        if self.get_value_for_configuration_key ('Time'):
            return int(self.get_value_for_configuration_key ('Time'))
        else:
            return False

