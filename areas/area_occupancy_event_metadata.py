'''

Area Occupancy Event Metadata

Interface to an Area item metadata

'''

from core.log import logging, LOG_PREFIX
log = logging.getLogger("{}.area_occupancy_event_metadata".format(LOG_PREFIX))
 
from org.eclipse.smarthome.core.items import ItemNotFoundException
from core.jsr223.scope import itemRegistry
import personal.occupancy.support.metadata_item_namespace
reload (personal.occupancy.support.metadata_item_namespace) 
from personal.occupancy.support.metadata_item_namespace import Metadata_Item_Namespace

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

    def get_lock_item(self):
        lock_item = None
        lock_item_name = self.get_value_for_configuration_key ('Lock')
        if lock_item_name != None:
            try:
                lock_item = itemRegistry.getItem(lock_item_name)
            except ItemNotFoundException:
                log.warn("Item {} is configured as a lock for area {}, but the item does not exist".format(lock_item_name, self.item_name))
        return lock_item
