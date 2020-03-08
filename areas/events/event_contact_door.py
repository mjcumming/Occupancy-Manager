'''

Process door contact change event. A door event sets uses the Open event to signal occupnacy
The Closed event starts the occupancy timer. Area is considered occupied until the door is closed.

Convert Open/Closed events to begin/end events for the area item 

'''


from core.log import logging, LOG_PREFIX
log = logging.getLogger("{}.item_event_contact".format(LOG_PREFIX))

import personal.occupancy.areas.events.event_base
reload (personal.occupancy.areas.events.event_base)
from personal.occupancy.areas.events.event_base import Event_Base


class Event_Contact_Door (Event_Base):

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

    #subclasses can override as needed
    def end_event(self, event):
        Event_Base.end_event(self,event)

        self.area.unlock()
        log.info ('Area {} unlocked, event ended'.format(self.area.name))
    












