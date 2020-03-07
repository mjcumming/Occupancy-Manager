'''

Process contact change event

Convert Open/Closed events to begin/end events for the area item 

'''

from core.log import logging, LOG_PREFIX
log = logging.getLogger("{}.item_event_contact".format(LOG_PREFIX))

import personal.occupancy.areas.events.event_base
reload (personal.occupancy.areas.events.event_base)
from personal.occupancy.areas.events.event_base import Event_Base


class Event_Contact (Event_Base):

    def process_changed_event(self,event):  

        Event_Base.process_changed_event(self,event)

        event_settings = self.get_event_settings() 
        item_state = str(event.itemState)
       
        if item_state == "OPEN": #begin event
            self.begin_event(event)

        elif item_state == "CLOSED": # off, an end event, only change occupancy settings if specified
            self.end_event(event)

        else:
            log.info ('Unknown contact event {}'.format(item_state)) # should not happen




    












