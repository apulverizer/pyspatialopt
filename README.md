# pyspatialopt
An open source python library for spatial optimization modeling. Be sure to check out the [wiki pages](https://github.com/apulverizer/pyspatialopt/wiki) for more information.

This library can be used to generate and solve spatial optimization models (in the form of .lp or .mps files) from spatial data. 
It has bindings for [arcpy](http://desktop.arcgis.com/en/arcmap/latest/analyze/arcpy/what-is-arcpy-.htm) and [pyqgis](http://docs.qgis.org/testing/en/docs/pyqgis_developer_cookbook/) to generate the coverage configurations which are then used to generate and solve various optimization models using [PuLP](http://www.coin-or.org/PuLP/).

Currently the main focus is on coverage modelling though other optimization models may be added over time. Coverage modeling is generally used to find the best spatial configuration of a set of facilities that provide some level of service to units of demand. It is often necessary to “cover” demand within a prescribed time or distance. For example, say the Salt Lake City Fire Department is looking to reduce the number of fire stations and wants to know how many fire stations are necessary to reach 90% of the houses within 5 minutes. We can use the Threshold Covering Problem to solve this problem. The facility layer would consist of the service area of each existing fire station. The demand layer would consist of the locations of the houses (or block group housing data). After solving the model, we can determine how many stations are required, the coverage provided by optimal configuration, and we can map the results. 

Another simple use case is shown in the image below. Suppose we have 7 possible facility locations (represented by the black triangles) and need to locate 5 facilities so that we get the most coverage. We can apply the MCLP to find the best configuration that reaches the most people (black-outlined polygons, Census block groups that have population). The service areas shown in green represent the 5 facilities that were selected by the model. The service areas shown in red, represent the 2 facilities that were not chosen. In this simple case it might be easy enough to try every possible configuration, but when we start to have hundreds to thousands of facilities, it becomes infeasible and an optimization model must be used.

![alt MCLP example](https://github.com/apulverizer/pyspatialopt/wiki/img/mclp_example.JPG "MCLP Example")

## Models

The following models are supported:

 * Maximum Coverage Location Problem (MCLP) 
    * Church, Richard, and Charles R. Velle. "The maximal covering location problem." Papers in regional science 32.1 (1974): 101-118.
 * Maximum Coverage Location Problem with Complementary Coverage (MCLPCC)
   * Tong, D. (2012). Regional coverage maximization: a new model to account implicitly for complementary coverage. Geographical Analysis, 44(1), 1-14.
 * Threshold Model
    * Church, Richard, and Alan Murray. 2009. Coverage. In Business Site Selection, Location Analysis, and GIS. Hoboken, New Jersey: Wiley.
 * Complementary Coverage Threshold Model
    * Church, Richard, and Alan Murray. 2009. Coverage. In Business Site Selection, Location Analysis, and GIS. Hoboken, New Jersey: Wiley.
    * Tong, D. (2012). Regional coverage maximization: a new model to account implicitly for complementary coverage. Geographical Analysis, 44(1), 1-14.
 * Backup Coverage Location Problem (BCLP)
    * Hogan, Kathleen, and Charles Revelle. 1986. Concepts and Applications of Backup Coverage. Management Science 32 (11):1434-1444.
 * Location Set Covering Problem (LSCP)
    * Toregas, Constantine, et al. "The location of emergency service facilities." Operations Research 19.6 (1971): 1363-1373.
 
 
#Workflow
1. Load a spatial data into a feature (vector) layer
2. Create a coverage(s) dictionary/json object by performing spatial operations to determine which facilities cover which demand areas (overlay, intersect ...)
3. Merge any coverages created, if you want to incorporate multiple facility types (optional)
4. Determine the serviceable demand assuming all facilities are used by performing spatial operations and update the coverage (optional)
5. Generate the desired model (optionally write to file)
6. Solve the model using whatever tools are supported py PuLP (Gurobi, GLPK...)
7. Do something with the results (Map them, get stats...)

#Example usage
The map shown above was derived from the results of this example.

```python
    import arcpy
    import pulp
    from pyspatialopt.models import covering, utilities
    from pyspatialopt.analysis import arcpy_analysis

    # Load shapefiles to feature layers
    demand_polygon_fl = arcpy.MakeFeatureLayer_management(r"../sample_data/demand_polygon.shp").getOutput(0)
    facility_service_areas_fl = arcpy.MakeFeatureLayer_management(r"../sample_data/facility_service_areas.shp").getOutput(0)
    
    # Generate the coverage and create the model
    binary_coverage_polygon = arcpy_analysis.generate_binary_coverage(demand_polygon_fl, facility_service_areas_fl, "Population", "GEOID10", "ORIG_ID")
    mclp = covering.create_mclp_model(binary_coverage_polygon, {"total": 5}, "mclp.lp")
    
    # Solve the model
    mclp.solve(pulp.GLPK())
    
    # Get the ids of facilities that were chosen and create a definition/selection query
    ids = utilities.get_ids(mclp, "facility_service_areas")
    select_query = arcpy_analysis.generate_query(ids, unique_field_name="ORIG_ID")
    facility_service_areas_fl.definitionQuery = select_query
    
    # Get the total amount of coverage provided (how many people were covered by this model)
    total_coverage = arcpy_analysis.get_covered_demand(demand_polygon_fl, "Population", "binary",
                                                       facility_service_areas_fl)
```
 
#Installation

**Note I have only tested the installation and funcationality of the library on Windows 10 though I see no reason why it won't work on \*nix and OSX systems.**

1. Clone/Fork the repo locally
2. Ensure that you have arcpy (ArcGIS) or pyqgis (QGIS) installed
3. Ensure that you download and install from [here](http://www.coin-or.org/PuLP/) or from source at [github](https://github.com/coin-or/pulp)
4. Run the setup.py script (```python setup.py install```)
5. Set the $QGIS_PATH (if you plan to use QGIS) environment variable to point to the directory containing your QGIS installation
6. Run the tests or examples to verify that it works. 

**If you are using PyQGIS you need make sure you have your PYTHONPATH pointed to the required QGIS directories**
 
 
#Notes
This is a side project and I will try to respond to issues and make updates but the code is provided as-is with no guarantees. 

Feel free to open issues if you need assistance, find a bug, or would like to request a new feature. Pull requests are welcomed.
