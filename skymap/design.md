# Design

## Concepts

A map consists of a collection of drawable objects (e.g. lines and circles). These are
defined in the map coordinate system, which has an arbitrary origin and is measured in mm. The
low-level implementation here is the `TikzPicture`. This low-level implementation should also
provide a way to perform clipping of objects using clipping paths defined in the map coordinate
system.

A higher level represents the sky, filled with more abstract objects defined in the sky
coordinate system. These objects represent the actual mapped objects like stars, but also the
parallels, meridians, equators and their ticks. These are basically single points or collections
of points, though these points may be approximations of shapes (e.g. circles and arcs). Apart
from one or more points, the objects can have additional properties, like brightness. 
The points belonging to an object can be projected into the map coordinate space. In some cases,
the abstract shape of the object can be projected. Just as the map domain, the sky domain should 
provide a way to perform clipping of objects using clipping paths defined in the sky coordinate
system.

Order of drawing:
- define the mapped sky area
- define the projection
- define the map size and shape  
- define all sky objects:
  - stars
  - meridians and ticks
  - parallels and ticks
  - equators and polar markers
- clip all sky objects to the mapped sky area
- project all sky objects to map objects
- add any other map objects
- clip all map object to the mapped area
- draw each object


## Map drawing interfaces

* Drawable objects: should have a draw method
  * Circle
  * Ellipse
  * Square
  * Rectangle
  * Line
  * Arc
  * ...
  
* Labelable objects
  
## Real objects vs map objects
Perhaps have real objects (stars, galaxies, etc), and the derived drawable map objects (star marker, galaxy marker).
The latter have the map coordinates and all drawing stuff, the former has the sky coordinates and all physical
characteristics.
  
## Map creation workflow
* Plot map area and gridlines
* Load objects from database (stars, galaxies, etc)
* Maybe precess objects and/or propagate proper motion
* Cluster objects (double/multiples), create composite object (replace the original objects with the composite object)
* Label objects
* Sort objects by decreasing brightness/size
* Loop over objects

## Newest idea
Create map with some config details. Add objects, with info on clipping. When rendering, project all objects, then do the clipping etc.

MapArea gets a MapConfig, part of the MapConfig is a CoordinateGridConfig.

MapConfig:
* latitude and longitude info
* projection
* map size and border info
* clipping info
* gridlines config

GridLinesConfig:
* drawing parameters (color, line thickness, pattern)
* grid line intervals
* ticks
* labels
* equators

Things to put on the paper:
* Map inner border (optional)
* Map outer border (optional)
* Meridians
  * Line
  * Longitude ticks
  * Longitude labels
  * Latitude ticks
  * Latitude labels
* Parallels
  * Line
  * Latitude ticks
  * Latitude labels
  * Longitude ticks
  * Longitude labels
* Equator(s)
  * Line
  * Longitude ticks
  * Longitude abels
  * Note: an equator is a special parallel, and its longitude ticks are even more special cases of meridians
* Pole(s)
  * Marker

###Inner and outer border
* Show true/false
* Linewidth
* Lower left corner
* Upper right corner
* Optional: horizontal and vertical margin between borders

###Meridians, parallels
* Line interval
* Labeled tick interval
* Tick interval
* Linewidth
* Ticks true/false per border
* Ticks rotated true/false per border
* Labeled tick size
* Unlabeled tick size
* Fixed tick reach true/false
* Labels rotated true/false per border
* Labels flipped true/false per border
* Label font
* Label fontsize
* Label text callback
* Label distance



