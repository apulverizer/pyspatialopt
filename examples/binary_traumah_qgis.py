# -*- coding: UTF-8 -*-
import logging
import os
import sys
import pulp
import qgis
from pyspatialopt.analysis import pyqgis_analysis
from pyspatialopt.models import covering
from pyspatialopt.models import utilities

if __name__ == "__main__":
    # Initialize a logger so we get formatted output
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    formatter = formatter = logging.Formatter('%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
    # setup stream handler to console output
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(formatter)
    logger.addHandler(sh)

    qgs = qgis.core.QgsApplication(sys.argv, True)
    qgs.setPrefixPath(os.path.expandvars(r"$QGIS_PATH"), True)
    qgs.initQgis()

    # Load layers
    dl_service_area = qgis.core.QgsVectorLayer(r"../sample_data/demand_polygon.shp", "demand_polygon_fl",
                                                      "ogr")
    dl = qgis.core.QgsVectorLayer(r"../sample_data/demand_point.shp", "demand_point_fl", "ogr")

    ad_layer = qgis.core.QgsVectorLayer(r"../sample_data/facility.shp",
                                                      "facility_point_fl", "ogr")
    tc_layer = qgis.core.QgsVectorLayer(r"../sample_data/facility2.shp",
                                                       "facility2_point_fl", "ogr")
    coverage = pyqgis_analysis.generate_traumah_coverage(dl, dl_service_area,
                                                                 tc_layer, ad_layer,
                                                                 "Population", 5000, dl_id_field="GEOID10",
                                                                 tc_layer_id_field="ID", ad_layer_id_field="ID")
    # Create the trauma Pulp linear programming problem
    # Use 5 Air Depot (Helicopter launch pads) and 10 Trauma Centers
    traumah = covering.create_traumah_model(coverage, 5, 10)

    # Solve the model using GLPK
    logger.info("Solving TRAUMAH...")
    traumah.solve(pulp.GLPK())

    # Get the unique ids of the 5 facilities chosen
    logger.info("Extracting results")
    ad_ids = utilities.get_ids(traumah, "AirDepot")
    tc_ids = utilities.get_ids(traumah, "TraumaCenter")
    # Generate a query that could be used as a definition query or selection in arcpy
    select_query = pyqgis_analysis.generate_query(ad_ids, unique_field_name="ID")
    select_query2 = pyqgis_analysis.generate_query(tc_ids, unique_field_name="ID")
    # Print the important results
    logger.info("Output query to use to generate maps (showing selected Air Depots) is: {}".format(select_query))
    logger.info("Output query to use to generate maps (showing selected Trauma Centers) is: {}".format(select_query2))
    logger.info("Total Population Covered: {}".format(pulp.value(traumah.objective)))

