# -*- coding: UTF-8 -*-
import logging
import os
import sys
import pulp
import qgis
from pyspatialopt.models import covering, utilities
from pyspatialopt.analysis import pyqgis_analysis

if __name__ == "__main__":
    # supply path to qgis install location
    qgs = qgis.core.QgsApplication(sys.argv, True)
    # Change this to your <QGIS installation paths>\apps\qgis
    qgs.setPrefixPath(os.path.expandvars(r"$QGIS_PATH"), True)
    qgs.initQgis()

    # Set the logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    formatter = formatter = logging.Formatter('%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(formatter)
    logger.addHandler(sh)

    # Read the layers
    demand_polygon_fl = qgis.core.QgsVectorLayer(r"../sample_data/demand_polygon.shp", "demand_polygon_fl", "ogr")
    facility2_service_areas_fl = qgis.core.QgsVectorLayer(r"../sample_data/facility2_service_areas.shp",
                                                          "facility2_service_areas_fl", "ogr")

    # Test partial coverage generation
    partial_coverage2 = pyqgis_analysis.generate_partial_coverage(demand_polygon_fl, facility2_service_areas_fl,
                                                                  "Population",
                                                                  "GEOID10", "ORIG_ID")

    # Create the model, minimize the number of facilities that still results in 80 percent coverage
    logger.info("Creating complemenatary coverage threshold model...")
    ccthreshold = covering.create_cc_threshold_model(partial_coverage2, 80, "ccthreshold.lp")
    # Solve the model
    logger.info("Solving CC threshold model...")
    ccthreshold.solve(pulp.GLPK())
    # Extract the ids
    logger.info("Extracting results")
    ids = utilities.get_ids(ccthreshold, "facility2_service_areas")
    select_query = pyqgis_analysis.generate_query(ids, unique_field_name="ORIG_ID")
    logger.info("Output query to use to generate maps is: {}".format(select_query))
    # Determine how much demand is covered by the results
    facility2_service_areas_fl.setSubsetString(select_query)
    total_coverage = pyqgis_analysis.get_covered_demand(demand_polygon_fl, "Population", "partial",
                                                        facility2_service_areas_fl)
    logger.info("{0:.2f}% of demand is covered".format((100 * total_coverage) / partial_coverage2["totalDemand"]))
