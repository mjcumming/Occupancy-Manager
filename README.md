**Occupancy Manager**

OpenHAB Community thread https://community.openhab.org/t/occupany-management-how-i-do-it/67961

**Introduction**


Home automation often relies on knowing if the home or an area of the home is occupied. Occupancy Manager simplifies home automation tasks by tracking the occupancy state of area (locations or rooms). The occupancy manager uses existing devices that generate events to determine occupancy state. Based on the state of an area (vacant or occupied) lights, HVAC, and media devices can be turned on or off.
 
Unfortunately, it is often difficult to determine if an area is occupied unless each area has dedicated presence sensors. However, many areas will have other devices within them that can be used to decide if an area is occupied or vacant. Events from these devices (i.e. light switches, audio/video devices, security devices including motion sensors or door contacts) are used to set an area occupied or vacant.

An area is a discrete location in a home that we want to track occupancy for. Areas can be arranged in a hierarchical (i.e. Home/Main Floor/Bathroom) fashion
which allows for more sophisticated management of occupancy control using event propagation. An area is given an occupancy time when an occupancy event occurs. For instance, in a bathroom, if a light switch is turned on, the bathroom is set to occupied for the duration of the occupancy time. The bathroom will remain
occupied until that time expires and then it will become vacant. When the bathroom becomes vacant, the lights and/or exhaust fan can be set to automatically turn off with no user programming or scripting. While the bathroom is occupied, if there additional events (i.e. a light switch is changed, the exhaust fan is turned on) the occupancy time is reset. 

The occupancy manager encapsulates all the logic needed to provide sophisticated occupancy-driven automation without requiring any additional programming. Item
tags and metadata are used to control the behavior of the occupancy manager. 

**Operation**

An area is a location/room/space that we want to track occupancy for. In OpenHAB each area is represented by a group item. It is beneficial (but not required) to
setup areas in a hierarchical fashion. The rationale for doing this is it allows for event propagation from child to parent areas and for control of occupancy
from parent to child areas. For instance, events in above example of a bathroom, are propagated to the Main Floor area, and to the Home and these areas remain occupied when their child area, the bathroom, updates it occupancy state.

**Areas**

Areas are defined in “.items” files as group items. Item metadata is used to determine the occupancy behavior for that area. Area metadata is stored in the namespace "OccupancySettings". The value for the namespace is not used and is set to "" . The namespace configuration values (text with the square brackets) determines area behavior.

Each area can have set of automatic actions that happen when its state (Occupied or Vacant) changes. Each area has a default occupancy time that is used to determine how long the area remains in an occupied state after an event in that area occurs. If no further occupancy events occur in that time, the area becomes vacant. Additionally, item events can be used to set an area vacant (i.e. a presence sensor indicates the area is vacant).

**Metadata settings:**

Time = number of minutes an area is occupied after an event that occurs that indicates the area is occupied.

VacantActions = actions to take when an area becomes vacant. Current allowed actions include LightsOff, SceneOff, AVOff, ExhaustFansOff

OccuppiedActions = action to take when an area becomes occupied. Current allowed actions include LightsOn, LightsOnIfDark, SceneOn, SceneOnIfDark

**Area Group Item Examples:**

```
Group gMF_Bathroom "Bathroom" (gIN_MainFloor)  {OccupancySettings = "" [Time = 15, VacantActions = "LightsOff,ExhaustFansOff" ]}
```

In this example, the area represents a bathroom. The **gMF_Bathroom** area is an area in the **gIN_MainFloor** area, i.e. the **gIN_MainFloor** area is the
parent area. When the bathroom area becomes occupied, the occupancy time is set to 15 minutes. This means that if there are no other events in that area (i.e. a
light switch changes or any other event that we track) the area will become vacant in 15 minutes. When the area becomes vacant, the VacantActions are
executed, which in this case means to turn off the lights and exhaust fans (more later how to set this up)

```
Group gIN_MainFloor "First Floor" (gHM_Interior) ["Area"] {OccupancySettings = "" [ Time = 120, VacantActions = "LightsOff" ]}
```

In this example, the area represents the main floor of the home. This area is child area of the gHM_Interior area. The area is occupied for 120 minutes when
there is any event in that area or any child areas (i.e. the bathroom above) change occupancy state. VacantActions are “LightsOff” which tells the occupancy
manager to turn off any lights in the gIN_MainFloor group with the item tag [“Lighting”].

```
Group gEX_Garage "Garage" (gHM_Exterior) ["Area"] {OccupancySettings = "" [ Time= 10, OccupiedActions = "SceneOnIfDark", VacantActions = "SceneOff" ]}
```

In this example, the garage, when it becomes occupied, the lights are turned on if it is dark outside. When the area becomes vacant, all the lights are turned off.

Ares may have any number of items that generate events that indicate that the area is occupied or vacant. For instance, turning a light switch on indicates that the area is occupied or if a motion sensor detects motion, then the area is occupied. Additionally, turning off a light switch can be used to change an area to vacant. Items (switches, sensors, or any device that generates an event) are added to the area group. More below.

Areas can be arranged in a hierarchical manner which allows for tracking of occupancy and subsequent actions across a range of areas.

For instance, if we have a home

1.  Home

    1.  First floor

        1.  Livingroom

        2.  Bathroom

        3.  Kitchen

    2.  Second floor

        1.  Bathroom

        2.  Bedroom 1

        3.  Bedroom 2

An occupancy event in the First Floor bathroom will automatically update the occupancy state and time of the First Floor and the Home. If, through a rule, the Home is set to Vacant, the vacancy event will propagate to all of the other areas and perform all the vacancy actions set in those areas. In short, setting item that represents the Home to vacant, all of the lights in the home could be turned off.

**Item Events**

Any OpenHAB item (device) can be used to set the occupancy or vacancy of an area. Items used change occupancy status are assigned to the group **gOccupancyItem**. This group is used in a rule to catch changes to its members and propagate that event to the occupancy manager. The **gOccupanyItem** group is created automatically by the occupancy manager.

Items used for occupancy use item metadata to determine how the events from the item change occupancy status. The namespace **OccupancyEvent** is set to the type of event that the item generates (examples below). Currently, there 4 types of predefined events that items can generate.

**OnOff** = Generates an occupancy event when the item is turned on (i.e. light switch). No event when the item is turned off.

**ContactMotion** = Generates an occupancy event when the contact is opened, no event when the contact closes

**ContactDoor** = Generates an occupancy event when the contact is opened, the area remains in an occupied state until the door is closed. The occupancy timer
starts when the door is closed.

**ContactPresence** = Generates an occupancy event when the contact is opened, the area remains in an occupied state until the sensor is closed. The area is
set to vacant immediately when the close event occurs.

**AnyChange** = Generates an occupancy event when the item state changes.

Switches (i.e. lights, power states) and Dimmer (lights, volume controls) items use the **OnOff** event. Contact items uses one of the 3 contact event types

In addition to generate events to set an area as occupied or vacant, there are metadata key/value pairs that are used to modify the standard behavior of the
predefined occupancy events. These key value pairs include BeginOccupiedTime and EndOccupiedTime. These additional settings allow overriding the default occupied
time for an area. Example below.

Metadata settings for items used in occupancy management:

OccupancyEvent = occupancy event type

Additional settings for using the configuration portion of the metadata include:

BeginOccupiedTime, minutes

EndOccupiedTime, minutes

Item Examples:

Dimmer
```
Dimmer  MF_PantryLight_Dimmmer "Pantry Light"  <light>     (gMF_Pantry,gLightSwitch,gOccupancyItem) ["Lighting"]   {channel="xxx", OccupancyEvent = OnOff"}                                                           
```

Switch
```
Switch	BM_AVReceiver_GeneralPower	"Power"	<receiver>	(gBM_RecRoom,gAVPower,gOccupancyItem)	{channel="xx", OccupancyEvent = "OnOff"}
```

```
Switch MF_MainFloorBathroom_Scene "Main Floor Bathroom Lights" (gMF_Bathroom,gOccupancyItem) ["Lighting"] {channel="xxx", OccupancyEvent = "OnOff"}
```

Contact
```
Contact  MF_FrontHallway_MotionSensor  "Front Hallway Motion"  <motion>   (gMF_FrontEntryHallway,gOccupancyItem) {channel="xx", OccupancyEvent = "ContactMotion"}
```

Any Change in State
```
String	ECHO_Kitchen_LastVoiceCommand	"Last voice command"	(gMF_Kitchen,gOccupancyItem)   {channel="xx", OccupancyEvent = "AnyChange"}
```



**Item Control**

Items to be controlled by the occupancy manager must be tagged so the occupancy manager can identify them. Current defined include Lighting, AreaScene, AVPower, ExhaustFan.

Item Examples:

```
Switch MF_MainFloorBathroom_Scene "Main Floor Bathroom Lights" (gMF_Bathroom ,gOccupancyItem) ["Lighting","AreaScene"] {channel="xxx", OccupancyEvent = "OnOff"}
```

In the example of above, this item, a lighting scene is tagged with AreaScene which is used to indicate to the occupancy manager to use this item to turn on/off lighting in this area when occupancy/vacancy events occur.

**Extended Functionality**

The occupancy manager automatically creates additional items that can be used to generate custom automation beyond the default behavior set in the occupancy manager. Documentation below to be expanded in the future.

**Occupancy State Item**

Each area includes an occupancy state item that generates On (occupied) or Off (vacant) events. These items are named OS_XXX, XXX set to the name of the area. These events can be used to trigger additional actions using standard OpenHAB rules. The occupancy state item for an area can also be used to set the occupancy state of that area in instances where the standard behavior of the occupancy manager does not meet the users needs.

**Occupancy Locking Item**

Each area includes an occupancy locking item. This item is represents the locking state of an area. These items are named OL_XXX, XXX set to the name of the area. This is used in situations where the user does not want item events to change the occupancy state of an area. For instance, a home maybe vacant and the user wants to turn on inside lights to make the home look occupied. In this instance, the user would not want the occupancy state of the home turned to occupied.

The occupancy locking items are NOT to be directly changed by external events or controls. Locking state is controlled by the occupancy control item below.

**Occupancy Control Item**

Each area includes an occupancy control item. These items are named OC_XXX, XXX set to the name of the area. This item is used to set the occupancy locking for that area. The occupancy control is set to LOCK or UNLOCK or CLEARLOCKS.

LOCK = lock the occupancy state of the area. Subsequent LOCK commands increase the level of locking.

UNLOCK = decreases the locking level of an area. When the locking level is 0 there area becomes unlocked.

CLEARLOCKS = Sets the locking level of an area to 0 and unlocks the area regardless of how many LOCK commands were sent.


INSTALLATION

Create a folder named occupancy in the automation/lib/python/personal folder. Copy these fills into the occupancy folder.

Also install the Item Metadata repository files https://github.com/mjcumming/Item-Metadata

Create a script in the automation/jsr232/python/personal folder called start_occupancy_manager.py 

```
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
```

           







