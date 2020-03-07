'''

On/Off event handler, includes dimmable items, with level 0 = off and > 0 = on

Converts On/Off events to begin/end events for the area item 


'''

from core.log import logging, LOG_PREFIX
log = logging.getLogger("{}.item_event_onoff".format(LOG_PREFIX))

import personal.occupancy.areas.events.event_base
reload (personal.occupancy.areas.events.event_base)
from personal.occupancy.areas.events.event_base import Event_Base

class Event_OnOff (Event_Base):

    def process_changed_event(self,event):  
        Event_Base.process_changed_event(self,event)     

        event_settings = self.get_event_settings() 

        item_state = str(event.itemState)
        try:
            percent = float(item_state) 
        except:
            percent = 0
        
        #log.warn('Area Item ON OFF event  State {}  Percent {}'.format(item_state,percent))

        if item_state == "ON" or percent > 0: #begin event
            self.begin_event(event)

        elif item_state == "OFF" or percent == 0: # off, an end event, only change occupancy settings if specified
            self.end_event(event)

        else:
            log.info ('Unknown on/off event {}'.format(item_state))
