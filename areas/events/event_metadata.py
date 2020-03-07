'''

Occupancy Event Metadata


ModifyBehavior - overrides default settings
    OnlyIfAreaVacant - the item will generate an occupancy event only if the area is currently vacant
    OverrideTimesIfVacant - item will override the default times of the area only if the area is currently vacant
    OccupiedUntilEnded- the item keeps the state of the area occupied until a closed event occurts (ie a door contact stays open)

Occupancy events can override the occupancy times specified in the area
    BeginOccupancyTime is set when the event begins
    EndOccupancyTime is set when the event ends

Begin events are typically On events that set or update the state of an area to Occupied
End events are typically none events or may be used to set an area to unoccupied to lower the time until
an area becomes vacent

''' 

import personal.metadata_item_namespace
reload (personal.metadata_item_namespace) 
from personal.metadata_item_namespace import Metadata_Item_Namespace

class Event_Metadata(Metadata_Item_Namespace):

    def __init__ (self, item_name):
        self.item_name = item_name
        self.namespace = "OccupancyEvent"

    def get_behaviors(self):
        return str.split(self.get_value_for_configuration_key('ModifyBehavior') or '',',')

    def only_if_vacant(self):
        self.read_raw()
        if "OnlyIfAreaVacant" in self.get_behaviors():
            return True
        else:
            return False

    def override_times_if_vacant(self):
        self.read_raw()
        if "OverrideTimesIfAreaVacant" in self.get_behaviors():
            return True
        else:
            return False
            
    def occupied_until_ended(self):
        self.read_raw()
        if "OccupiedUntilEnded" in self.get_behaviors():
            return True
        else:
            return False

    def get_begin_occupied_time(self):
        return self.get_value_for_configuration_key('BeginOccupiedTime')

    def get_end_occupied_time(self):
        return self.get_value_for_configuration_key('EndOccupiedTime')
