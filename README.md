Occupancy Manager

Introduction

Occupancy Manager simplifies home automation tasks. Controlling the automated home is often based on knowning whether an area of the home is occuppied. Based on the state of an area (vacant or occupied) lights, HVAC, and media devices can be turned on or off.

Unfortunately, it is often difficult to determine if an area is occuppied unless each area has dedicated presence sensor. However, many areas will have items within them that can be used to decide if an area is occuppied. Events from these sensors (light sitches, audio video devices, security devices including motion sensors or door contacts) are used to set an area occuppied or vacant.

An area is a discrete loction in a home that we want to track occupancy for. Areas can be arranged in a hierarchial fashion which allows for more sophisticated management of occupancy control.

The occupancy manager allows easy setup of areas, items, and behaviors with essentially no programming

Operation

An area is a location/room/space that we want to track occupancy for. In OpenHAB each area is represented by a group item. Areas can be setup in an hierarchial fashion which allows for more sophisticated automation.

Areas can be defined in .items files or via the PaperUI. Areas are tagged using the tag "Area". This allows the occupancy manager to find areas it is to manage. Settings that determine the behaviour of an area are set in the group items metadata. Each area can have set of actions depending on its occupancy state. Each area has a default occupancy time when an event that indicates occupancy occurs.

Area metadata is in the namespace "OccupancySettings". The value for the namespace is set to "" (it is unused). The namespace configuration values (text with the square brackets) determines area behaviour.

Time = number of minutes an area is occuppied after an event that occurs that indicates the area is occuppied.
VacantActions = actions to take when an area becomes vacant. Current allowed actions include LightsOff, SceneOff, AVOff, ExhaustFansOff
OccuppiedActions = action to take when an area becomes occuppied. Current allowed actions include LightsOn, LightsOnIfDark, SceneOn, SceneOnIfDark

Area Examples:

Group gMF_Bathroom "Bathroom" <bath> (gIN_MainFloor) ["Area"] {OccupancySettings = "" [ Time = 15, VacantActions = "LightsOff,ExhaustFansOff" ]}

In this example, the area represents a bathroom. The area is a space in the gIN_MainFloor area. When the area becomes occuppied, the occupancy time is set to 15 minutes. This means that if there are no other events in that area (ie light switch changes) the area will become vacant in 15 minutes. When the area becomes vacant, the VacantActions are executed, which in this case means to turn the lights and exhaust fans (more later on how to set this up)

Group gIN_MainFloor "First Floor" <groundfloor> (gHM_Interior) ["Area"] {OccupancySettings = "" [ Time = 120, VacantActions = "LightsOff" ]}

In this example, the area represents the main floor of the home. The area is occuppied for 120 minutes when there is any event in that area or when any child areas (the bathroom above) change occupancy state.

Group gEX_Garage "Garage" <none> (gHM_Exterior) ["Area"] {OccupancySettings = "" [ Time = 10, OccupiedActions = "SceneOnIfDark", VacantActions = "SceneOff" ]}

In this example, the garage, when it becomes occupied, the lights are turned on if it is dark outside. When the area becomes vacant, all the lights are turned off

Each area/room is a unique Group which contains the Item in the area. These areas are members of the Group (gArea) and the gHome group which
the layout of the home.

Ares may have any number of items that generate events that indicate that the area is occupied. For instance, turning a light switch on indicates
that the area is occupied or if a motion sensor detects motion, than the area is occupied.

OCCUPANCY EVENT ITEMS

Items that can change occupancy status are members of the group gOccupancyItem. This group is used in a rule to catch changes to its members.
These items have Tags that indicate how occupancy is changed by events from that item. These tags start with OE:XXX.

Occupancy Event Items Tags
OE:Light_Standard = standard event from a Light item. When a light is turned ON then the area is set to occupied. When a light is turned OFF no change in occupancy
OE:Motion_Standard = standard event from a motion sensor, motion detected = occupied, no change when no motion

OCCUPANCY STATE ITEMS -> only used to check state DO NOT USE TO SET STATE

Each area must have an occupancy state item. This item is name OS_XXX, XXX = the name of the area. ON = occupied, off = VACANT
Changes to the occupancy state of an area are propagated to the sub areas of that item. Changes to a child area occupancy
state are propagated to the parent item(s). The OS item uses Tags to control behaviour of that area.

Occupancy State Item Tags
OccupancyTime:XX XX = minutes that the area is occupied
OccupancyAction:XX = actions to take when area is occupied
VacantAction:XX = actions to take when area is vacant

    ie. the tag OccupancyTime_XXX determines the number of minutes an area is to be in an
    occupied state after an item in that area indicates the area is occupied.

OCCUPANCY LOCKING ITEMS

Each area must have an occupancy locking item. This item is named OL_XXX, XXX = the name of the area. ON = locked, OFF = unlocked

The occupancy locking items are _NOT_ to be directly changed by external events or controls. Locking state is controled by the occupancy control below.
This extra control is required to allow for an area to be "LOCKED" by more than one automation event.

OCCUPANCY CONTROL

Each area must have an item that is used to control occupancy locking. The item declaration must start with OC_XXX and must be a
member of that area's group.

Occupancy Control item events
LOCK = Area occupancy status is set to locked, no events will change the area occupied status until unlocked
UNLOCK = Area is unlocked, occpuancy events will change status
CLEARLOCKS = Remove all locks


INSTALLATION

Place these files in the automation/lib/python/personal folder

Also install the Item Metadata repository files

Create a script in the automation/jsr232/python/personal folder called start_occupancy_manager.py 

import traceback

from org.slf4j import Logger, LoggerFactory  
log = LoggerFactory.getLogger("org.eclipse.smarthome.model.script.Rules") 

# start the occupancy manager  
try:
    import personal.occupancy.occupancy_manager
    reload (personal.occupancy.occupancy_manager) 
    import personal.occupancy.occupancy_manager 

except:
    log.error (traceback.format_exc())

           