# pyspatialopt
An open source python library for spatial optimization modeling

This library can be used to generate spatial optimization models (in the form of .lp files) from spatial data. 
Currently it uses the arcpy library (though QGIS, GDAL and other bindings may be added) to  generate the coverage models (json files) which are then used to generate different optimization models.

Currently the main focus is on coverage modelling though other optimization models may be added over time. 
The following models are supported:

 * Maximum Coverage Location Problem (MCLP) 
    * Church, Richard, and Charles R. Velle. "The maximal covering location problem." Papers in regional science 32.1 (1974): 101-118.
 * Threshold Model
    * Church, Richard, and Alan Murray. 2009. Coverage. In Business Site Selection, Location Analysis, and GIS. Hoboken, New Jersey: Wiley.
 * Complementary Coverage Threshold Model
    * Tong, D. (2012). Regional coverage maximization: a new model to account implicitly for complementary coverage. Geographical Analysis, 44(1), 1-14.
 * Backup Coverage Location Problem (BCLP)
    * Church, R., & Murray, A. (2009). Coverage Business Site Selection, Location Analysis, and GIS (pp. 209-233). Hoboken, New Jersey: Wiley.
 * Location Set Covering Problem (LSCP)
    * Church, R., & Murray, A. (2009). Coverage Business Site Selection, Location Analysis, and GIS (pp. 209-233). Hoboken, New Jersey: Wiley.
 
 
#Workflow
1. Create a coverage(s) dictionary/json object by performing spatial operations to determine which facilities cover which demand areas (overlay, intersect ...)
2. Merge any coverages created (optional)
3. Determine the serviceable demand assuming all facilities are used by performing spatial operations and update the coverage (optional)
4. Generate the desired model and write to file
5. Solve the model using whatever tools can solve lp files (Gurobi, CPLEX...) since we use pulp to generate the problems, any of their supported CLI and API hooks will work
6. Do something with the results (Map them, get stats...)
 
#Notes
This is a side project and I will try to respond to issues and make updates but the code is provided as-is with no guarantees. 

Feel free to open issues if you need assistance, find a bug, or would like to request a new feature. Pull requests are welcomed.