# -*- coding: UTF-8 -*-
import arcpy
from analysis import arcpy_analysis
import json
import logging
from models import covering
import pulp
import sys


def get_ids(problem, variable_name, threshold=1.0, delineator="$"):
    """
    helper to get the variables
    :param problem: (pulp problem) The solved problem to extract results from
    :param variable_name: (string) The variable name to extract
    :param threshold: (float) The minimum value to use when chooing ids
    :param delineator: (string) The string used to split demand and facilities from ids
    :return:
    """
    ids = []
    for var in problem.variables():
        if var.name.split(delineator)[0] == variable_name:
            if var.varValue >= threshold:
                ids.append(var.name.split("$")[1])
    return ids


if __name__ == "__main__":
    arcpy.env.overwriteOutput = True
    arcpy.env.workspace = r"C:\Users\apulv\Documents\ArcGIS\Default.gdb"

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    formatter = formatter = logging.Formatter('%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

    # setup stream handler to console output
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(formatter)
    logger.addHandler(sh)

    # Write the results to files
    with open("partial_coverage1.json", "r") as f:
        partial_coverage = json.load(f)
    with open("binary_coverage_polygon1.json", "r") as f:
        binary_coverage_polygon = json.load(f)
    with open("binary_coverage_point1.json", "r") as f:
        binary_coverage_point = json.load(f)

    with open("partial_coverage2.json", "r") as f:
        partial_coverage2 = json.load(f)
    with open("binary_coverage_polygon2.json", "r") as f:
        binary_coverage_polygon2 = json.load(f)
    with open("binary_coverage_point2.json", "r") as f:
        binary_coverage_point2 = json.load(f)

    with open("serviceable_demand_polygon.json", "r") as f:
        serviceable_demand_polygon = json.load(f)
    with open("serviceable_demand_point.json", "r") as f:
        serviceable_demand_point = json.load(f)

    logger.info("Creating MCLP model...")
    mclp = covering.create_mclp_model(binary_coverage_polygon, {"total": 5}, "mclp.lp")
    logger.info("Solving MCLP...")
    mclp.solve(pulp.GUROBI())
    logger.info("Extracting results")
    ids = get_ids(mclp, "facility_service_areas")
    select_query = arcpy_analysis.generate_query(ids, unique_field_name="FID")
    logger.info("Output query to use to generate maps is: {}\n".format(select_query))

    logger.info("Creating threshold model...")
    threshold = covering.create_threshold_model(binary_coverage_point2, 30, "threshold.lp")
    logger.info("Solving threshold model...")
    threshold.solve(pulp.GUROBI())
    logger.info("Extracting results")
    ids = get_ids(threshold, "facility2_service_areas")
    select_query = arcpy_analysis.generate_query(ids, unique_field_name="FID")
    logger.info("Output query to use to generate maps is: {}\n".format(select_query))

    logger.info("Creating complemenatary coverage threshold model...")
    ccthreshold = covering.create_cc_threshold_model(partial_coverage2, 80, "ccthreshold.lp")
    logger.info("Solving CC threshold model...")
    ccthreshold.solve(pulp.GUROBI())
    logger.info("Extracting results")
    ids = get_ids(ccthreshold, "facility2_service_areas")
    select_query = arcpy_analysis.generate_query(ids, unique_field_name="FID")
    logger.info("Output query to use to generate maps is: {}\n".format(select_query))

    logger.info("Creating backup model...")
    merged_dict = covering.merge_coverages([binary_coverage_point, binary_coverage_point2])
    merged_dict = covering.update_serviceable_demand(merged_dict, serviceable_demand_point)
    bclp = covering.create_backup_model(merged_dict, {"total": 30}, "backup.lp")
    logger.info("Solving backup model...")
    bclp.solve(pulp.GUROBI())
    logger.info("Extracting results")
    ids = get_ids(bclp, "facility_service_areas")
    ids2 = get_ids(bclp, "facility2_service_areas")
    select_query = arcpy_analysis.generate_query(ids, unique_field_name="FID")
    select_query2 = arcpy_analysis.generate_query(ids2, unique_field_name="FID")
    logger.info("Output query to use to generate maps is: {}".format(select_query))
    logger.info("Output query2 to use to generate maps is: {}\n".format(select_query2))

    logger.info("Creating LSCP model...")
    merged_dict = covering.merge_coverages([binary_coverage_point, binary_coverage_point2])
    merged_dict = covering.update_serviceable_demand(merged_dict, serviceable_demand_point)
    lscp = covering.create_lscp_model(merged_dict, "lscp.lp")
    logger.info("Solving LSCP model...")
    lscp.solve(pulp.GUROBI())
    logger.info("Extracting results")
    ids = get_ids(lscp, "facility_service_areas")
    ids2 = get_ids(lscp, "facility2_service_areas")
    select_query = arcpy_analysis.generate_query(ids, unique_field_name="FID")
    select_query2 = arcpy_analysis.generate_query(ids2, unique_field_name="FID")
    logger.info("Output query to use to generate maps is: {}".format(select_query))
    logger.info("Output query to use to generate maps is: {}\n".format(select_query2))

