
import core
from core import osgi
from core import metadata
from core.jsr223.scope import itemRegistry

from core.log import logging, LOG_PREFIX
log = logging.getLogger("{}.area_manager".format(LOG_PREFIX))
 
import personal.occupancy.areas.area  
reload (personal.occupancy.areas.area) 
from personal.occupancy.areas.area import Area 
from personal.occupancy.areas.area_lock import Area_Lock 


#build group structure for occupancy items
supporting_groups = {
    'gOccupancy' : 'gContext',
    'gOccupancyItem' : 'gOccupancy', # Items that generate events that indicate occupancy are placed in this group, used to capture events from items 
    'gOccupancyState' : 'gOccupancy', # occupancy state of area, ON = occupied, OFF = vacant, add OS_XXX to its corresponding area 
    'gOccupancyControl' : 'gOccupancy', #used to send commands to set the behavior of the area, add OC_XXX items to the area
    'gOccupancyLocking' : 'gOccupancy', # represents whether an area is locked or not
    'gOccupancyLock' : 'gOccupancy' # area groups in this group lock other area groups
}
 
 
class Area_Manager:

    __OCCUPANCY_LOCK_GROUP = "gOccupancyLock"

    def __init__(self):
        log.warn('Area Manager Starting')

        self.areas = {} # dictionary of all areas indexed by area name
        self.area_locks = []
        self.commands = {} # track commands per trigger

        self.setup_supporting_groups() # support group
        self.setup_areas()

    def setup_supporting_groups(self): # add supporting groups from dictionary above
        for groupname,parentgroup in supporting_groups.iteritems():
            items = itemRegistry.getItems(groupname)
 
            if items.size() == 0:
                item = core.items.add_item (groupname,item_type="Group", groups=[parentgroup])
                metadata.set_value(item.name,"Source","Occupancy") # set metadata to indicate we created this group

    def add_area(self,area_item, is_lock):
        area_class = Area_Lock if is_lock else Area
        area = area_class(area_item,self.areas) 
        self.areas [area_item.name] = area
        if is_lock:
            self.area_locks.append(area)
        log.info ('Added {} {}'.format(area_class.__name__, area_item))
        
    def is_configured_as_lock(self,item):
        # members of the occupancy lock group are considered locks
        for groupName in item.getGroupNames():
            if groupName == Area_Manager.__OCCUPANCY_LOCK_GROUP:
                return True
        return False

    def setup_areas(self):
        items = itemRegistry.getItems()

        for item in items:
            if metadata.get_value(item.name,"OccupancySettings") is not None: # add any group with the metadata key OccupancySettings
                self.add_area(item, self.is_configured_as_lock(item))
        log.info ('Found Areas: {}'.format(self.areas))
        
        # link locks to their areas
        for area_lock in self.area_locks:
            for parent in area_lock.get_parent_area_groups():
                parent.set_lock(area_lock)
                
    def get_group_area_item_for_item(self,item_name): # finds the area that an item belongs to
        item = itemRegistry.getItem(item_name)

        for group_name in item.getGroupNames (): # find the group occupancy area item for this item
            if metadata.get_value(group_name,"OccupancySettings") is not None: 
                area_item = itemRegistry.getItem(group_name)
                log.info ('Item {} is in area {}'.format (item.name,area_item.name))
                return area_item
                 
        return None
 
    def get_area_for_item(self,item_name): # get an Area instance that correspsonds to the area for the item
        area_item = self.get_group_area_item_for_item(item_name) #get the area_item that this item belongs too

        if not area_item:
            log.info ('Item {} does not belong to an Area.'.format(item_name))
            return False

        if not self.areas.has_key(area_item.name): # create instance if needed
            self.add_area(area_item)
        
        return self.areas [area_item.name]
 
    def process_item_changed_event(self,event):
        # We process trigger events only if we can't correlate them to a previous command
        if not self.correlate_command(event.itemName, event.itemState):
            area = self.get_area_for_item(event.itemName)
            log.info ('Item Event {} Area {}.'.format(event,area))
            if area:
                area.process_item_changed_event (event)        
        else:
            log.debug("Swallowed trigger changed event {} for {}".format(event.itemState, event.itemName))

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
            
    # If an item triggers occupancy but also receives resulting actions then we must not interpret the resulting action as a new trigger event.
    # A trigger event is identified by just an item state update without any item command. 
    # A resulting action is identified by an item command and a subsequent item state update. 
    # Unfortunately we have no means of deterministically correlating an item command and the resulting state update.
    # The best we can do is to assume that an item command will be followed by a matching item state change before other commands or state changes are processed. 
    # So if we receive a command we record the command for the trigger for future matching.
    # If we receive a state update we check if this state change is the result of a previous command, i.e. if that command was recorded. 
    # If it was recorded we swallow the state update. If it wasn't recorded we conclude the state update happened in isolation and process it. 
    # We always clear the recorded state after a state update in case our assumptions didn't hold due to timing of events or binding behavior. 

    # Record commands for a trigger for future matching
    def record_command(self,trigger_item_name,state):
        self.commands[trigger_item_name] = state;
        
    # Return true if we can correlate the provided state for a trigger with a previously recorded command, false otherwise
    def correlate_command(self,trigger_item_name,state):
        correlate = self.commands.get(trigger_item_name) == state;
        self.commands[trigger_item_name] = None
        return correlate


#Area_Manager()