'''

Occupancy Event 

Represents an Item that causes events in an Area

Items have metadata to determine their effect on the oocupancy state of an area

Occupancy events always have a begining and most will have an ending

Ie. a contact sensor becoming open is the begining of an event 
and closing is the end of event

Ie. a light turning on is the begining of an event, turning
off is the end of the event
 
Metadata

ModifyBehavior - overrides default settings
    OnlyIfAreaVacant - the item will generate an occupancy event if the area is currently vacant
    OverrideTimesIfAreaVacant - item will override the default times of the area only if the area is currently vacant
    OccupiedUntilEnded the item keeps the state of the area occupied until a this event ends (ie a door contact that is open keeps the area occupied until the end event when the door closes)

Occupancy events can override the occupancy times specified in the area
    BeginOccupancyTime is set when the event begins
    EndOccupancyTime is set when the event ends

Begin events are typically On events that set or update the state of an area to Occupied
End events are typically none events (we do not use them) or may be used to set an area to unoccupied to lower the time until
an area becomes vacant 

 
'''
from core.log import logging, LOG_PREFIX
log = logging.getLogger("{}.area_item_event".format(LOG_PREFIX))

import personal.occupancy.areas.events.event_metadata 
reload (personal.occupancy.areas.events.event_metadata)
from personal.occupancy.areas.events.event_metadata import Event_Metadata


class Event_Base():

    name = None # name of the area group that we are tracking occupancy for
    item = None # the group for the area
    last_event = None # last event we received from the item

    def __init__(self, item, area):
        self.item = item
        self.item_name = str(item.name)
        self.area = area 

    def get_event_settings(self): #gets metadata settings
        return Event_Metadata(self.item_name)     

    def process_changed_event(self,event):
        self.last_event = event   

    def begin_event(self, event):
        if not self.area.is_locked(): # check if area locked before proceeding with standard events
            event_settings = self.get_event_settings()

            if event_settings.only_if_vacant() and self.area.is_area_occupied(): # item will generate an occupancy event if the area is currently vacant
                log.info('Ignoring item {} event as area is occuppied already and only if area vacant flag is present'.format(self.item_name))
                return

            override_occupancy_time = event_settings.get_begin_occupied_time() # set to None if time not specified

            if self.area.is_area_occupied() and event_settings.override_times_if_vacant(): # area occupied and settings specified to only use item occupancy if area vacant
                log.info('Ignoring item {} event time as area is occuppied already'.format(self.item_name))
                override_occupancy_time = None

            log.info('Using item {} event time {}'.format(self.item_name,override_occupancy_time))

            self.area.set_area_occupied (self.item_name,override_occupancy_time)
            if event_settings.occupied_until_ended(): # lock the area until an end event comes from this item
                self.area.lock()

        else:
            log.info ("Area {} is locked, no change made to occupancy status".format(self.area.name))

    def end_event(self, event):
        event_settings = self.get_event_settings()

        if not self.area.is_locked(): # check if area locked before proceeding with standard events
            override_occupancy_time = event_settings.get_end_occupied_time()

            if override_occupancy_time: #override default time 
                self.area.set_area_occupied (self.item_name,override_occupancy_time)
            # otherwise, do nothing, as end events typically do not indicate a change in state unless a time is specified
        
        elif event_settings.occupied_until_ended ():
            self.area.unlock()
            log.info ('Area {} locked until occupancy event ends'.format(self.area.name))

        else:
            log.info ("Area {} is locked, no change made to occupancy status".format(self.area.name))
