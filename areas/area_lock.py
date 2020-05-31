'''

Area_Lock Class

A specialized Area that serves as a lock for its parent Areas.
If an Area_Lock is occupied then its parent Areas are considered locked.

'''

import core
from personal.occupancy.areas.area import Area 
from core.jsr223.scope import ON


class Area_Lock(Area):

    def propagates_events(self):
        return False # locks never propagate events
        
    def process_occupancy_state_changed_event(self,event): # if lock gets set cancel timers for the areas we control
        if event.itemState == ON:
            for parent_area in self.get_parent_area_groups():
                parent_area.cancel_timer()
        
        super(Area_Lock,self).process_occupancy_state_changed_event(event)