'''

Process presence contact change event. A presence event sets uses the Open event to signal occupnacy
The Closed event ends the occupancy. Area is considered occupied until the door is closed.

Convert Open/Closed events to begin/end events for the area item 

'''

from org.slf4j import Logger, LoggerFactory

log = LoggerFactory.getLogger("org.eclipse.smarthome.model.script.Rules")

import personal.occupancy.areas.events.event_base
reload (personal.occupancy.areas.events.event_base)
from personal.occupancy.areas.events.event_base import Event_Base

class Event_Contact_Presence (Event_Base):
    def process_changed_event(self,event):  

        Event_Base.process_changed_event(self,event)

        item_state = str(event.itemState)
       
        if item_state == "OPEN": #begin event
            self.begin_event(event)

        elif item_state == "CLOSED": # off, an end event, only change occupancy settings if specified
            self.end_event(event)

        else:
            log.info ('Unknown contact event {}'.format(item_state)) # should not happen

    def begin_event(self, event):
        Event_Base.begin_event(self,event)

        log.info ('Area {} locked, until event ends'.format(self.area.name))
        self.area.lock()

    def end_event(self, event):
        Event_Base.end_event(self,event)

        self.area.unlock()
        self.area.set_area_vacant ('Presence sensor CLOSED')

        log.info ('Area {} unlocked and set to vacant, presence event ended'.format(self.area.name))
    












