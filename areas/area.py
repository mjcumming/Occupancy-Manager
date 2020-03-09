'''

Area Class

Used to manage occupancy

Represents a physical location and manages all events for items that happen in the area related to occupancy/vacancy control

Handles events that occur from items located within an area to determine occupancy state
 

'''
 
import datetime
from threading import Timer

import core.items 
from core.jsr223.scope import itemRegistry
from core.jsr223.scope import events   
from core import osgi

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
log = logging.getLogger("{}.area".format(LOG_PREFIX))

import personal.occupancy.areas.area_occupancy_event_metadata
reload (personal.occupancy.areas.area_occupancy_event_metadata)
from personal.occupancy.areas.area_occupancy_event_metadata import Area_Occupancy_Event_Metadata

import personal.occupancy.areas.events.item_event_handler
reload (personal.occupancy.areas.events.item_event_handler)
from personal.occupancy.areas.events.item_event_handler import Item_Event_Handler


supporting_item_prefixes = {
    "OS" : "gOccupancyState",
    "OC" : "gOccupancyControl",
    "OL" : "gOccupancyLocking"
}

supporting_item_types = {
    "OS" : "Switch",
    "OC" : "String",
    "OL" : "Switch"
}

def send_command (item,command):
    if item.type == 'Dimmer':
        if command == 'ON':
            command = 100
        elif command == 'OFF':
            command = 0

    events.sendCommand (item,command)


class Area:

    name = None # name of the area group that we are tracking occupancy for
    item = None # the group item for this area

    last_event_item = None # last event that triggered occupancy

    occupancy_timer = None # timer that is used to count down occupancy
    occupancy_timeout = None # if not None represents the time the timer will fire at
    time_left_when_locked = None # residual time on timer when room locked, used to restore timer after unlock

    locking_level = 0 # number of times an area has been locked, 0 = unlocked

    occupancy_control_item = None # OC item for the area

    occupancy_state_item = None # OS item for the area

    occupancy_locking_item = None # OL itemt for the area

    area_event_handler = None # handler to deal with item events

    def __init__(self,name, area_list):
        log.info ('Initializing Area {}'.format(name))
        self.name = str(name)
        self.area_list = area_list

        self.item = itemRegistry.getItem(self.name)
        
        self.item_event_handler = Item_Event_Handler (self) # used to process events from an item in the area
        
        self.setup_supporting_items () # support group items

        self.occupancy_settings = Area_Occupancy_Event_Metadata(self.name) # reads the group item metadata to determine how occupancy functions

    def __str__(self):
        ot = self.occupancy_timeout or 'Vacant'
        return 'Area: {}, Occupied until = {}, {}'.format(self.name, ot, (self.is_locked() and 'Locked' or 'Unlocked'))

    def setup_supporting_items(self):
        base_name = self.name [1:] # remove the 'g'

        for prefix,parentgroup in supporting_item_prefixes.iteritems():
            item_name = prefix+'_'+base_name
            items = itemRegistry.getItems(item_name)

            if items.size() == 0:
                log.info ('Adding supporting items... Item {}, Parent {}'.format(item_name,parentgroup))
                item = core.items.add_item (item_name,item_type=supporting_item_types [prefix], groups=[parentgroup,self.name])
                
                if not MetadataRegistry.get(MetadataKey('Source',item.name)): # tag the item so we know we created it
                    MetadataRegistry.add(Metadata(MetadataKey('Source',item.name),'Occupancy',{}))        

        self.occupancy_control_item = self.get_occupancy_control_item_for_area(self.name)
        self.occupancy_state_item = self.get_occupancy_state_item_for_area(self.name)
        self.occupancy_locking_item = self.get_occupancy_locking_item_for_area(self.name)

    def get_occupancy_state_item_for_area(self,name):
        return itemRegistry.getItem(str("OS_"+name [1:]))

    def get_occupancy_control_item_for_area(self,name):
        return itemRegistry.getItem(str("OC_"+name [1:]))

    def get_occupancy_locking_item_for_area(self,name):
        return itemRegistry.getItem(str("OL_"+name [1:]))

    def start_timer(self, time_out_seconds):
        time_started = datetime.datetime.now()

        def timeout_callback():
            log.info("Occupancy timer for area {} expired, timer was started at {}".format(self.name,time_started)) 
            self.set_area_vacant('Timer Expired')
            self.occupancy_timer = None
            self.occupancy_timeout = None        

        if self.occupancy_timer is not None:
            #log.info("Occupancy timer for area {} canceled".format(self.name)) 
            self.occupancy_timer.cancel()
            self.occupancy_timer = None
            self.occupancy_timeout = None

        self.occupancy_timer = Timer(time_out_seconds, timeout_callback)
        self.occupancy_timer.start()
        self.occupancy_timeout = datetime.datetime.now() + datetime.timedelta(seconds=time_out_seconds)
        log.warn("Occupancy Timer for area {} expires at {}".format(self.name,self.occupancy_timeout))

    def cancel_timer(self):
        #log.info ("Occupancy timer for area {} canceled".format(self.name))
        if self.occupancy_timer is not None:
            self.occupancy_timer.cancel()
            self.occupancy_timer = None
            self.occupancy_timeout = None

    def get_parent_area_group(self): # finds a parent area for areas list if there is one
        #names = list (group_name for group_name in self.item.getGroupNames () if "Area" in itemRegistry.getItem (group_name).getTags ()) 
        #names = list (group_name for group_name in self.item.getGroupNames () if MetadataRegistry.get(MetadataKey('OccupancySettings',group_name)))

        for group_name in self.item.getGroupNames ():
            if MetadataRegistry.get(MetadataKey('OccupancySettings',group_name)):
                parent_area = self.area_list [group_name]
                return parent_area

        return None
     
    def get_child_area_group_items(self):
        child_groups = []
        for child_item in self.item.members:
            #if "Area" in child_item.getTags():
            if MetadataRegistry.get(MetadataKey('OccupancySettings',child_item.name)):
                child_groups.append(child_item)

        return child_groups

    def is_locked(self): # returns true if area is locked
        if self.locking_level>0:
            return True
        else:
            return False

    def lock(self):
        self.locking_level = self.locking_level + 1
        if self.locking_level == 1: # went from unlocked to locked, manage area timer
            if self.occupancy_timeout: # timer was running, store time remaining
                self.time_left_when_locked =self.occupancy_timeout - datetime.datetime.now() # save time left
                log.info("Occupancy Locking turned on, time left in minutes {}".format(int(self.time_left_when_locked.seconds/60)))
            # cancel running timer
            self.cancel_timer()

        # update locking state
        events.postUpdate (self.occupancy_locking_item,'ON') 

    def unlock(self):
        self.locking_level = self.locking_level - 1

        if self.locking_level == 0: # area unlocked
            # restart timer if time was left on it
            if self.time_left_when_locked is not None:
                if self.is_area_occupied(): #area occupied, restart timer
                    log.info("Occupancy Locking turned off for area {}, Timer restarted with time left {} minutes ".format (self.name,int(self.time_left_when_locked.seconds/60)))  
                    self.start_timer(self.time_left_when_locked.seconds)  
            else:
                log.info("Occupancy Locking turned off for area {}, area vacant and timer NOT restarted".format (self.name))  

        if self.locking_level < 0:
            self.locking_level = 0

        # update locking state
        if self.locking_level == 0:
            events.postUpdate (self.occupancy_locking_item,'OFF') 

    def clear_lock(self):
        self.locking_level = 1
        self.unlock() # executes above without repeating code here

    def start_lock_timer(self, time_out_seconds):

        def timeout_callback():
            log.warn("Occupancy LOCK timer for area {} expired".format(self.name)) 
            self.unlock()

        self.lock_timer = Timer(time_out_seconds, timeout_callback)
        self.lock_timer.start()
        log.warn("Occupancy LOCK timer for area {} started for {} seconds".format(self.name,time_out_seconds))

    def is_area_occupied (self):
        if str(self.occupancy_state_item.state) == 'ON':
            return True
        else:
            return False
    
    def update_group_OS_item(self,state): # use updates to change OS state, commands are sent from external actions/scripts
        events.postUpdate(self.occupancy_state_item,state) # post update NOT send command, exteral actions in scripts use send command to set OS state

    def set_area_occupied(self,reason,occupancy_time = None):
        if not self.is_locked(): # check if area locked before proceeding 
            occupancy_time = occupancy_time or self.occupancy_settings.get_occupancy_time()

            if occupancy_time is not None:
                occupancy_time = int(occupancy_time)

            log.info("Area {} is occupied, triggering item {}, using occupancy time of {} ".format (self.name,reason,occupancy_time))
            # set or update occupancy timer as required
            if not occupancy_time: # we did not get a time we can use or one was not specified
                log.info('No occupancy time specified for area {} occupied event.'.format(self.name))
            elif occupancy_time > 0: 
                self.start_timer(occupancy_time*60)  
                self.update_group_OS_item('ON')
            elif occupancy_time == 0: # got an occupancy item event specifying off, ie time 0
                self.set_area_vacant('Occupancy Time 0') 
                return # do not propagate an "off" event to parent areas (below)
            else:#invalid number
                log.info('Invalid occupancy time {} for area {} occupied event.'.format(occupancy_time,self.name))
        else:
            log.info ('Area {} is locked'.format(self.name))

        #propagate event to parent area
        parent_area = self.get_parent_area_group() 
        log.info ('Area {} is propagting event to {}'.format(self.name,parent_area))
        if parent_area:
            parent_area.set_area_occupied ("Child Area Event")
 
    def set_area_vacant(self,reason):
        log.info("Set Area {} to vacant, reason {}".format (self.name,reason))

        if not self.is_locked(): # check if area locked before proceeding 
            self.update_group_OS_item('OFF')
            self.cancel_timer() # cancel any running timers

            # when area is vacant, force child areas to vacant
            for child_item in self.item.members:
                #if "Area" in child_item.getTags():
                if MetadataRegistry.get(MetadataKey('OccupancySettings',child_item.name)):
                    area = self.area_list [child_item.name]
                    log.info ("Propagating occupancy state to child area {}".format(child_item.name))
                    area.set_area_vacant ('Parent Vacant')
        
        else: # note we cannot really fix this here, user needs to not set an area vacant if it is locked ** may need to change this behavior
            log.info ('Area {} is locked.'.format(self.name))

    # ------------------------ event handlers events related to occupancy, called from the occupancy manager ------------------------

    def process_item_changed_event(self,event): # an item that is a member of this area changed, update OS, reset area timer as required
        self.item_event_handler.process_item_changed_event(event) #dispatch to handler, this will update OS state using area and item metadata

    def process_occupancy_state_received_command_event(self,event): # OS command event handler, external command that change the OS of an area
        log.info("Area {} state received direct command from OS item".format (self.name,event.itemCommand))
        if str(event.itemCommand) == 'ON':
            self.set_area_occupied('Direct OS Command')
        else:
            self.set_area_vacant('Direct OS Command')
        
    def process_occupancy_state_changed_event(self,event): # OS event handler when the area's OS group item changes, execute Occupied or Vacant Actions
        if self.occupancy_settings.exists(): # must have these to proceed
            state = str(event.itemState)
            log.info("Occupancy state changed to {} ---->>> Settings for area {}: {} ".format (state, self.name,self.occupancy_settings))

            if not self.is_locked(): # check if area locked before proceeding 
                if state == 'ON':
                    actions = self.occupancy_settings.get_occupied_actions()
                    # perform any actions
                    for action in actions:
                        #log.info ('for loop {}'.format(action))
                        if action == "LightsOn": 
                            for item in self.item.members:
                                for tag in item.getTags():
                                    if tag=="Lighting":
                                        send_command (item,'ON')

                        elif action == "LightsOnIfDark":
                            if (itemRegistry.getItem ("VT_DayLight_Switch").state) == 'OFF':
                                for item in self.item.members:
                                    for tag in item.getTags():
                                        if tag=="Lighting":
                                            send_command (item,'ON')

                        elif action == "SceneOn": 
                            for item in self.item.members:
                                for tag in item.getTags():
                                    if tag=="AreaScene":
                                        events.sendCommand (item,'ON')

                        elif action == "SceneOnIfDark":
                            if str(itemRegistry.getItem ("VT_DayLight_Switch").state) == 'OFF':
                                for item in self.item.members:
                                    for tag in item.getTags():
                                        if tag=="AreaScene":
                                            events.sendCommand (item,'ON')
                        else:
                            log.info ('Unknown action {} in area {}'.format(action,self.name))

                # OFF = vacant, do any vacant actions
                elif state == 'OFF':
                    actions = self.occupancy_settings.get_vacant_actions()
                    # Process any actions based 'ON' the tags for that area
                    for action in actions:
                        #log.info ('Action {}'.format (action))
                        if action == "LightsOff": 
                            for item in self.item.members:
                                for tag in item.getTags():
                                    if tag=="Lighting":
                                        send_command (item,'OFF')

                        elif action == "SceneOff": 
                            for item in self.item.members:
                                for tag in item.getTags():
                                    if tag=="AreaScene":
                                        events.sendCommand (item,'OFF')

                        elif action == "ExhaustFansOff": 
                            for item in self.item.members:
                                for tag in item.getTags():
                                    if tag=="ExhaustFan":
                                        events.sendCommand (item,'OFF')

                        elif action == "AVOff": 
                            for item in self.item.members:
                                for tag in item.getTags():
                                    if tag=="AVPower":
                                        events.sendCommand (item,'OFF')
                        else:
                            log.info ('Unknown action {} in area {}'.format(action,self.name))

            else:#area locked
                log.info ("Area {} is locked, occupancy state changed, should not happen".format(self.name))
                #self.update_group_OS_item(,event.oldItemState) **** cannot do this results in endless event loop
                #if event.oldItemState == 'ON': # do not allow area to be vacant if it was on and locked
                 #   self.update_group_OS_item('ON',item)
        else: 
            log.info ("Area {} has no settings".format(self.name))

    def process_occupancy_locking_changed_event(self,event): #OL event handler, just a log event, no actions to be taken
        log.info("Occupancy Locking Changed for area {} to {}".format(self.name,event.itemState))
        # no event propagation, all occupancy locking should only be done via the occupancy control item

    def process_occupancy_control_received_command_event(self,event): # OC event handler for a command from OL to control area locking
        log.info("Occupancy Control for area {} received command {}".format(self.name,event.itemCommand))
        parts = str(event.itemCommand).split(',')
        command = parts [0]        

        if command == "LOCK":
            self.lock()
            if len(parts) == 2:
                timeout = int(parts[1])
                self.start_lock_timer(timeout)

        elif command == "UNLOCK":
            self.unlock()

        elif command == "CLEARLOCKS":
            self.clear_lock()

        elif command == "LOG":
            log.info (''.format(self))
            return
    
        log.info("Occupancy locking level for area {} is {}".format(self.name,self.locking_level))
    
        # propagate to child areas
        for child_item in self.get_child_area_group_items():
            log.info ("Propagating occupancy control {} to child area {}".format(event.itemCommand,child_item.name))
            events.sendCommand (self.get_occupancy_control_item_for_area(child_item.name),event.itemCommand)


