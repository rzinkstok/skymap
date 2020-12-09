# Design

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
  *  
