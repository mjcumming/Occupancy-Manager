""" 
  
Occupancy Manager     
       
Used to handle events from items that are used to determine and control occupancy
 
Dispatches the events to the area manager
                                       
"""                             
  
from core.jsr223.scope import scriptExtension
scriptExtension.importPreset("RuleSimple")
scriptExtension.importPreset("RuleSupport")
scriptExtension.importPreset("RuleFactories")
import core
from core.triggers import when
from core.rules import rule
from core import osgi 
from core import items   



from core.log import logging, LOG_PREFIX
log = logging.getLogger("{}.occupancy_manager".format(LOG_PREFIX))
 
# load the area manager class  
import personal.occupancy.areas.area_manager
reload (personal.occupancy.areas.area_manager) 
from personal.occupancy.areas.area_manager import Area_Manager      
  

#start the area manager
am = Area_Manager() 


    

#register event handlers

   
""" 
Receives events from items in an area 
   
Used to determine the occupancy state of an area

The type of occupancy event is set in the metadata of the item generating the event

gOccupancyItem group contains any items that generate events that might change the occupancy state 
"""
 
@rule ("gOccupancy Item Changed")  
@when ("Member of gOccupancyItem changed")

def gOccupancyItemChanged (event):
    log.warn ('Occupancy item changed {} {}'.format(event,event.oldItemState))

    #if event.oldItemState == UnDefType.NULL: # avoid events from persistance
    #    return

    am.process_item_changed_event (event)

"""
Responds to changes in the occupancy state of an area

Manages Occupancy/Vacancy actions

Propagates state to parent and/or child areas 
"""
    
@rule ("gOccupancy State Changed")
@when ("Member of gOccupancyState changed")

def gOccupancyStateChanged (event):
 
    #if event.oldItemState == UnDefType.NULL: # avoid events from persistance
    #    return 
    
    am.process_occupancy_state_changed_event (event) 
     

"""

Captures all commands to an area's occupancy state OS item 
 
"""
 
@rule ("gOccupancy State Command")
@when ("Member of gOccupancyState received command")
 
def gOccupancyStateReceivedCommand (event):
 
    am.process_occupancy_state_received_command_event (event)
   
            
@rule ("gOccupancy Locking Changed") 
@when ("Member of gOccupancyLocking changed")

def gOccupancyLockingChanged (event):

    #if event.oldItemState == UnDefType.NULL: # avoid events from persistance
    #    return 

    am.process_occupancy_locking_changed_event (event) # simply logs the event, does not do any processing
        

  
"""  
The occupancy control is used to send "commands" that change the behavior of an area

We use this control to Lock or Unlock an area

We can also clear all locks in the area

Changes made to a parent area are propagated to child areas
""" 

@rule ("gOccupancy Control Received Command")
@when ("Member of gOccupancyControl received command")

def gOccupancyControlReceivedCommand (event):
         
    am.process_occupancy_control_received_command_event (event)
         

def scriptUnloaded():
    """ Clears out all existing timers on script unload."""
    am.script_unload()
