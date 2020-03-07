'''

handles events from an item in an area and dispatches to appropriate handler

used by area.py

'''

from core.log import logging, LOG_PREFIX
log = logging.getLogger("{}.area_item_event_handler".format(LOG_PREFIX))

# pylint: disable=import-error
from core.jsr223.scope import itemRegistry 
# pylint: enable=import-error 

# load the classes
import personal.occupancy.areas.events.event_metadata
reload (personal.occupancy.areas.events.event_metadata)
from personal.occupancy.areas.events.event_metadata import Event_Metadata

import personal.occupancy.areas.events.event_onoff
reload (personal.occupancy.areas.events.event_onoff)
from personal.occupancy.areas.events.event_onoff import Event_OnOff

import personal.occupancy.areas.events.event_contact
reload (personal.occupancy.areas.events.event_contact)
from personal.occupancy.areas.events.event_contact import Event_Contact

import personal.occupancy.areas.events.event_anychange
reload (personal.occupancy.areas.events.event_anychange)
from personal.occupancy.areas.events.event_anychange import Event_AnyChange

event_to_class = {
    'OnOff' : Event_OnOff, #includes dimmer items, 0 = OFF, > 0 = ON
    'Contact' : Event_Contact, #contact items, ie Open/Close
    'AnyChange' : Event_AnyChange, #contact items, ie Open/Close
}


class Item_Event_Handler():
    
    area = None # area that we are working with
    area_item_event_handlers = None #dictionary of event handlers, indexed by item name

    def __init__(self, area):
        self.area = area
        self.area_item_event_handlers = {} 

    def process_item_changed_event(self, event):
        item_name = str(event.itemName)

        occupancy_event = Event_Metadata (item_name)
        log.warn("Item {} in Area {} changed to {}. Event settings -->> {}".format (item_name, self.area.name, event.itemState,occupancy_event))

        if occupancy_event.exists():# item has appropriate metadata,process the event and create an instance of item process event
            if item_name not in self.area_item_event_handlers: 
                event_type = occupancy_event.get_value ()

                if event_to_class.has_key(event_type):
                    item = itemRegistry.getItem(item_name)
                    handler = event_to_class [event_type] (item,self.area)
                    self.area_item_event_handlers [item_name] = handler

                else:
                    log.warn ("Unknown occupancy event type {}".format (occupancy_event.get_value()))
                    return

           # if occupancy_event.only_if_vacant() and self.area.is_area_occupied():
           #     log.info('Ignoring item event as area is occuppied already and only if area vacant flag is present')
           #     return

            self.area_item_event_handlers [item_name].process_changed_event(event)
        else:
            log.warn('No occupancy settings found for item {}'.format(item_name))      
            return

