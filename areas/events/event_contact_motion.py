'''

Process  motion contact change event. A motion event sets uses the Open event to signal occupnacy
The Closed event is ignored.

Convert Open/Closed events to begin/end events for the area item 

'''

from org.slf4j import Logger, LoggerFactory

log = LoggerFactory.getLogger("org.eclipse.smarthome.model.script.Rules")

import personal.occupancy.areas.events.event_base
reload (personal.occupancy.areas.events.event_base)
from personal.occupancy.areas.events.event_base import Event_Base


class Event_Contact_Motion (Event_Base):

    def process_changed_event(self,event):  

        Event_Base.process_changed_event(self,event)

        item_state = str(event.itemState)
       
        if item_state == "OPEN": #begin event
            self.begin_event(event)

        elif item_state == "CLOSED": # off, an end event, only change occupancy settings if specified
            self.end_event(event)

        else:
            log.info ('Unknown contact event {}'.format(item_state)) # should not happen




    












