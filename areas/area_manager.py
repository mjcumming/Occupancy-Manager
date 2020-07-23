
import core
from core import osgi
from core import metadata
from core.jsr223.scope import itemRegistry

from core.log import logging, LOG_PREFIX
log = logging.getLogger("{}.area_manager".format(LOG_PREFIX))

log.warn('Area Manager Loaded')
 
# load the area Class  
import personal.occupancy.areas.area  
reload (personal.occupancy.areas.area) 
from personal.occupancy.areas.area import Area 


#build group structure for occupancy items
supporting_groups = {
    'gOccupancy' : 'gContext',
    'gOccupancyItem' : 'gOccupancy', # Items that generate events that indicate occupancy are placed in this group, used to capture events from items 
    'gOccupancyState' : 'gOccupancy', # occupancy state of area, ON = occupied, OFF = vacant, add OS_XXX to its corresponding area 
    'gOccupancyControl' : 'gOccupancy', #used to send commands to set the behavior of the area, add OC_XXX items to the area
    'gOccupancyLocking' : 'gOccupancy', # represents whether an area is locked or not
}

class Area_Manager:

    areas = {} # dictionary of all areas indexed by area name

    def __init__(self):
        log.warn('Area Manager Starting')

        self.setup_supporting_groups() # support group
        self.setup_areas()

    def setup_supporting_groups(self): # add supporting groups from dictionary above
        for groupname,parentgroup in supporting_groups.iteritems():
            items = itemRegistry.getItems(groupname)
 
            if items.size() == 0:
                item = core.items.add_item (groupname,item_type="Group", groups=[parentgroup])
                metadata.set_value(item.name,"Source","Occupancy") # set metadata to indicate we created this group

    def add_area(self,area_item):
        self.areas [area_item.name] = Area(area_item,self.areas) 
        log.info ('Added area {}'.format(area_item))

    def setup_areas(self):
        items = itemRegistry.getItems()

        for item in items:
            if metadata.get_value(item.name,"OccupancySettings") is not None: # add any group with the metadata key OccupancySettings
                self.add_area(item)

        log.info ('Found Areas: {}'.format(self.areas))

    def get_group_area_item_for_item(self,item_name): # finds the area that an item belongs to
        item = itemRegistry.getItem(item_name)

        for group_name in item.getGroupNames (): # find the group occupancy area item for this item
            if metadata.get_value(group_name,"OccupancySettings") is not None: 
                area_item = itemRegistry.getItem(group_name)
                log.info ('Item {} is in area {}'.format (item.name,area_item.name))
                return area_item
                 
        return None
 
    def get_group_areas_item_for_item(self,item_name): # finds the areas that an item belongs to
        item = itemRegistry.getItem(item_name)

        area_list = []
        for group_name in item.getGroupNames (): # find the group occupancy area item for this item
            if metadata.get_value(group_name,"OccupancySettings") is not None: 
                area_item = itemRegistry.getItem(group_name)
                log.info ('Item {} is in area {}'.format (item.name,area_item.name))
                area_list.append (area_item)
                 
        return area_list
        
    def get_area_for_item(self,item_name): # get an Area instance that correspsonds to the area for the item
        area_item = self.get_group_area_item_for_item(item_name) #get the area_item that this item belongs too

        if not area_item:
            log.info ('Item {} does not belong to an Area.'.format(item_name))
            return False

        if not self.areas.has_key(area_item.name): # create instance if needed
            self.add_area(area_item)
        
        return self.areas [area_item.name]

    def get_areas_for_item(self,item_name): # get an Area instance(s) that correspsonds to the area for the item
        area_items = self.get_group_areas_item_for_item(item_name) #get the area_items that this item belongs too

        areas = []
        for area_item in area_items:
            if not self.areas.has_key(area_item.name): # create instance if needed
                self.add_area(area_item)
            areas.append(self.areas[area_item.name])

        return areas

    def process_item_changed_event(self,event):
        #area = self.get_area_for_item(event.itemName)
        #log.info ('Area {} Item Event {}.'.format(area,event))
        #if area:
        #    area.process_item_changed_event (event)        
        
        area_list = self.get_areas_for_item(event.itemName)
        log.warn ('Item Event {} in Areas {}.'.format(event,area_list))
        for area in area_list:
            area.process_item_changed_event (event)        

    def process_occupancy_state_changed_event(self,event):
        area = self.get_area_for_item(event.itemName)
        if area:
            area.process_occupancy_state_changed_event(event)        

    def process_occupancy_state_received_command_event(self,event):
        area = self.get_area_for_item(event.itemName)
        if area:
            area.process_occupancy_state_received_command_event(event)        
 
    def process_occupancy_locking_changed_event(self,event):
        area = self.get_area_for_item(event.itemName)
        if area:
            area.process_occupancy_locking_changed_event(event) # simply logs the event, does not do any processing
    
    def process_occupancy_control_received_command_event(self,event):
        area = self.get_area_for_item(event.itemName)
        if area:
            area.process_occupancy_control_received_command_event(event)
         
    def script_unload(self):
        for area_name,area in self.areas.items():
            log.warn ('Area {} timer canceled {}.'.format(area_name,area))
            area.cancel_timer()

#Area_Manager()