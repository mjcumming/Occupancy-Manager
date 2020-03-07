'''

AnyChange event handler

Generates occupancy event on any change to the item


'''

from core.log import logging, LOG_PREFIX
log = logging.getLogger("{}.item_event_anychange".format(LOG_PREFIX))

import personal.occupancy.areas.events.event_base
reload (personal.occupancy.areas.events.event_base)
from personal.occupancy.areas.events.event_base import Event_Base

class Event_AnyChange (Event_Base):

    def process_changed_event(self,event):  
        Event_Base.process_changed_event(self,event)     

        self.begin_event(event)
