import core
from core import osgi
from core.jsr223.scope import itemRegistry

try:
    from org.openhab.core.items import Metadata, MetadataKey
except:
    from org.eclipse.smarthome.core.items import Metadata, MetadataKey

MetadataRegistry = osgi.get_service(
        "org.openhab.core.items.MetadataRegistry"
    ) or osgi.get_service(
        "org.eclipse.smarthome.core.items.MetadataRegistry"
    ) 

from core.log import logging, LOG_PREFIX
log = logging.getLogger("{}.area_manager".format(LOG_PREFIX))
 


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
        self.setup_supporting_groups() # support group
        self.setup_areas()

    def setup_supporting_groups(self):
        for groupname,parentgroup in supporting_groups.iteritems():
            items = itemRegistry.getItems(groupname)
 
            if items.size() == 0:
                log.info ('GN {}, PN {}'.format(groupname,parentgroup))
                item = core.items.add_item (groupname,item_type="Group", groups=[parentgroup])
                log.info('{}'.format(item))
                log.info(MetadataRegistry.get(MetadataKey('Source',item.name)))

                if not MetadataRegistry.get(MetadataKey('Source',item.name)):
                    MetadataRegistry.add(Metadata(MetadataKey('Source',item.name),'Occupancy',{}))

    def setup_areas(self):
        items = itemRegistry.getItems()

        for item in items:
            if 'Area' in item.getTags():
                self.areas [item.name] = Area(item.name,self.areas) 

    def get_group_area_for_item(self,item_name): # finds the area that an item belongs to
        item = itemRegistry.getItem(item_name)
        area_names = list (group_name for group_name in item.getGroupNames () if "Area" in itemRegistry.getItem (group_name).getTags ()) 

        if not area_names: # no matching area for item
            return None

        area_item = itemRegistry.getItem(area_names[0])
        #log.info ('Item {} is in area {}'.format (item.name,area_item.name))
        return area_item

    def get_area_for_item(self,item_name): # get an Area instance that correspsonds to the area for the item
        area_item = self.get_group_area_for_item(item_name) #get the area_item that this item belongs too

        if not area_item:
            log.info ('Item {} does not belong to an Area.'.format(item_name))
            return False

        if not self.areas.has_key(area_item.name): # create instance if needed
            self.areas [area_item.name] = Area(area_item.name,self.areas)
            item = itemRegistry.getItem(item_name)
            log.info ('Area {} added.'.format(item))
        
        return self.areas [area_item.name]
 
    def process_item_changed_event(self,event):
        area = self.get_area_for_item(event.itemName)
        log.warn ('Item Event {} Area {}.'.format(event,area))
        if area:
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
            log.warn ('Area timer canceled {}.'.format(area))
            area.cancel_timer()

Area_Manager()