# -*- coding: UTF-8 -*-
import logging
import math
import os

import arcpy

from pyspatialopt import version


def generate_query(unique_ids, unique_field_name, wrap_values_in_quotes=False):
    """
    Generates a select or definition query that can applied to the input layers
    :param unique_ids: (list) A list of ids to query
    :param unique_field_name: (string) The name of field that the ids correspond to
    :param wrap_values_in_quotes: (bool) Should the ids be wrapped in quotes (if unique_field_name is string)
    :return: (string) A query string that can be applied to a layer
    """
    if unique_ids:
        if wrap_values_in_quotes:
            query = "{} in (-1,{})".format(unique_field_name, ",".join("'{0}'".format(w) for w in unique_ids))
        else:
            query = "{} in (-1,{})".format(unique_field_name, ",".join(unique_ids))
    else:
        query = "{} in (-1)".format(unique_field_name)
    return query


def reset_layers(*args):
    """
    Clears the selection and definition query applied to the layers
    :param args: (Feature Layers) The feature layers to reset
    :return:
    """
    for layer in args:
        arcpy.SelectLayerByAttribute_management(layer, "CLEAR_SELECTION")
        layer.definitionQuery = ""


def generate_serviceable_demand(dl, dl_demand_field, dl_id_field, *args):
    """
    Finds to total serviceable coverage when 2 facility layers are used
    Merges polygons & dissolves them to form one big area of total coverage
    Then intersects with demand layer. Only used for partial coverages
    :param dl: (Feature Layer) The demand polygon or point layer
    :param dl_demand_field: (string) The field representing demand
    :param dl_id_field: (string) The name of the unique field for the demand layer
    :param args: (Feature Layer) The facility layers to use
    :return: (dictionary) A dictionary of similar format to the coverage format
    """
    # Reset DF
    # Check parameters so we get useful exceptions and messages
    reset_layers(dl)
    reset_layers(*args)
    if arcpy.Describe(dl).shapeType not in ["Polygon", "Point"]:
        raise TypeError("Demand layer must have polygon geometry")
    dl_field_names = [f.name for f in arcpy.Describe(dl).fields]
    if dl_demand_field not in dl_field_names:
        raise ValueError("'{}' field not found in demand layer".format(dl_demand_field))
    if dl_id_field not in dl_field_names:
        raise ValueError("'{}' field not found in demand layer".format(dl_id_field))
    # Check that all facility layers are polygon
    for fl in args:
        if arcpy.Describe(fl).shapeType != "Polygon":
            raise TypeError("{} is not a polygon layer".format(fl.desc.name))
    if fl is None:
        raise ValueError("No facility service area feature layers specified")
    dl_desc = arcpy.Describe(dl)
    logging.getLogger().info("Initializing output...")
    if dl_desc.shapeType == "Polygon":
        output = {
            "version": version.__version__,
            "demand": {},
            "type": {
                "mode": "serviceableDemand",
                "type": "partial"}
        }
    elif dl_desc.shapeType == "Point":
        output = {
            "version": version.__version__,
            "demand": {},
            "type": {
                "mode": "serviceableDemand",
                "type": "binary"}
        }
    else:
        raise TypeError("Demand layer must be point or polygon")
    logging.getLogger().info("Combining facilities...")
    dissovled_geom = None
    for layer in args:
        with arcpy.da.SearchCursor(layer, ['SHAPE@']) as fcursor:
            for f in fcursor:
                if dissovled_geom is None:
                    dissovled_geom = f[0]
                dissovled_geom = dissovled_geom.union(f[0])
    logging.getLogger().info("Determining possible service coverage for each demand unit...")
    with arcpy.da.SearchCursor(dl, [dl_id_field, dl_demand_field, "SHAPE@"]) as dcursor:
        if arcpy.Describe(dl).shapeType == "Polygon":
            for d in dcursor:
                if not dissovled_geom.disjoint(d[2]):
                    intersected = dissovled_geom.intersect(d[2], 4)
                    if intersected.area > 0:
                        serviceable_demand = math.ceil(
                            float(intersected.area / d[2].area) * d[1])
                    else:
                        serviceable_demand = 0.0
                else:
                    serviceable_demand = 0.0
                # Make sure serviceable is less than or equal to demand, floating point issues
                if serviceable_demand < d[1]:
                    output["demand"][str(d[0])] = {"serviceableDemand": serviceable_demand}
                else:
                    output["demand"][str(d[0])] = {"serviceableDemand": d[1]}
        else:  # Point
            for d in dcursor:
                intersected = dissovled_geom.intersect(d[2], 1)
                if intersected.centroid:  # check if valid
                    serviceable_demand = d[1]
                else:
                    serviceable_demand = 0.0
                output["demand"][str(d[0])] = {"serviceableDemand": serviceable_demand}
    logging.getLogger().info("Serviceable demand successfully created.")
    reset_layers(dl)
    reset_layers(*args)
    return output


def generate_binary_coverage(dl, fl, dl_demand_field, dl_id_field, fl_id_field, fl_variable_name=None):
    """
    Generates a dictionary representing the binary coverage of a facility to demand points
    :param dl: (Feature Layer) The demand polygon or point layer
    :param fl: (Feature Layer) The facility service area polygon layer
    :param dl_demand_field: (string) The name of the field in the demand layer that describes the demand
    :param dl_id_field: (string) The name of the unique identifying field on the demand layer
    :param fl_id_field: (string) The name of the unique identifying field on the facility layer
    :param fl_variable_name: (string) The name to use to represent the facility variable
    :return: (dictionary) A nested dictionary storing the coverage relationships
    """
    # Check parameters so we get useful exceptions and messages
    if arcpy.Describe(dl).shapeType not in ["Polygon", "Point"]:
        raise TypeError("Demand layer must have polygon or point geometry")
    if arcpy.Describe(fl).shapeType != "Polygon":
        raise TypeError("Facility service area layer must have polygon geometry")
    dl_field_names = [f.name for f in arcpy.Describe(dl).fields]
    if dl_demand_field not in dl_field_names:
        raise ValueError("'{}' field not found in demand layer".format(dl_demand_field))
    if dl_id_field not in dl_field_names:
        raise ValueError("'{}' field not found in demand layer".format(dl_id_field))
    fl_field_names = [f.name for f in arcpy.Describe(fl).fields]
    if fl_id_field not in fl_field_names:
        raise ValueError("'{}' field not found in facility service area layer".format(fl_id_field))
    reset_layers(dl, fl)
    if fl_variable_name is None:
        fl_variable_name = os.path.splitext(os.path.basename(arcpy.Describe(fl).name))[0]
    logging.getLogger().info("Initializing facilities in output...")
    output = {
        "version": version.__version__,
        "type": {
            "mode": "coverage",
            "type": "binary",
        },
        "demand": {},
        "totalDemand": 0.0,
        "totalServiceableDemand": 0.0,
        "facilities": {fl_variable_name: []}
    }
    # List all of the facilities
    with arcpy.da.SearchCursor(fl, [fl_id_field]) as cursor:
        for row in cursor:
            output["facilities"][fl_variable_name].append(str(row[0]))
    # Build empty data structure
    with arcpy.da.SearchCursor(dl, [dl_id_field, dl_demand_field, "SHAPE@AREA"]) as cursor:
        for row in cursor:
            output["demand"][str(row[0])] = {
                "area": round(row[2]),
                "demand": round(row[1]),
                "serviceableDemand": 0,
                "coverage": {fl_variable_name: {}}
            }
    logging.getLogger().info("Determining binary coverage for each demand unit...")
    with arcpy.da.SearchCursor(fl, [fl_id_field, "SHAPE@"]) as fcursor:
        if arcpy.Describe(dl).shapeType == "Point":
            for f in fcursor:
                with arcpy.da.SearchCursor(dl, [dl_id_field, "SHAPE@"]) as dcursor:
                    for d in dcursor:
                        if not f[1].disjoint(d[1]):
                            output["demand"][str(d[0])]["serviceableDemand"] = \
                                output["demand"][str(d[0])]["demand"]
                            output["demand"][str(d[0])]["coverage"][fl_variable_name][str(f[0])] = 1
        else:  # Polygon
            for f in fcursor:
                with arcpy.da.SearchCursor(dl, [dl_id_field, "SHAPE@"]) as dcursor:
                    for d in dcursor:
                        if not f[1].disjoint(d[1]):
                            if f[1].contains(d[1]):
                                output["demand"][str(d[0])]["serviceableDemand"] = \
                                    output["demand"][str(d[0])]["demand"]
                                output["demand"][str(d[0])]["coverage"][fl_variable_name][str(f[0])] = 1
    with arcpy.da.SearchCursor(dl, [dl_id_field, dl_demand_field]) as cursor:
        for row in cursor:
            output["totalServiceableDemand"] += output["demand"][str(row[0])]["serviceableDemand"]
            output["totalDemand"] += row[1]
    logging.getLogger().info("Binary coverage successfully generated.")
    reset_layers(dl, fl)
    return output


def generate_partial_coverage(dl, fl, dl_demand_field, dl_id_field="OBJECTID", fl_id_field="OBJECTID",
                              fl_variable_name=None):
    """
    Generates a dictionary representing the partial coverage (based on area) of a facility to demand areas
    :param dl: (Feature Layer) The demand polygon layer
    :param fl: (Feature Layer) The facility service area polygon layer
    :param dl_demand_field: (string) The name of the field in the demand layer that describes the demand
    :param dl_id_field: (string) The name of the unique identifying field on the demand layer
    :param fl_id_field: (string) The name of the unique identifying field on the facility layer
    :param fl_variable_name: (string) The name to use to represent the facility variable
    :return: (dictionary) A nested dictionary storing the coverage relationships
    """
    # Reset DF
    # Check parameters so we get useful exceptions and messages
    if arcpy.Describe(dl).shapeType != "Polygon":
        raise TypeError("Demand layer must have polygon geometry")
    if arcpy.Describe(fl).shapeType != "Polygon":
        raise TypeError("Facility service area layer must have polygon geometry")
    dl_field_names = [f.name for f in arcpy.Describe(dl).fields]
    if dl_demand_field not in dl_field_names:
        raise ValueError("'{}' field not found in demand layer".format(dl_demand_field))
    if dl_id_field not in dl_field_names:
        raise ValueError("'{}' field not found in demand layer".format(dl_id_field))
    fl_field_names = [f.name for f in arcpy.Describe(fl).fields]
    if fl_id_field not in fl_field_names:
        raise ValueError("'{}' field not found in facility service area layer".format(fl_id_field))
    reset_layers(dl, fl)
    if fl_variable_name is None:
        fl_variable_name = os.path.splitext(os.path.basename(arcpy.Describe(fl).name))[0]
    # Create the initial data structure
    logging.getLogger().info("Initializing facilities in output...")
    output = {
        "version": version.__version__,
        "type": {
            "mode": "coverage",
            "type": "partial",
        },
        "demand": {},
        "totalDemand": 0.0,
        "totalServiceableDemand": 0.0,
        "facilities": {fl_variable_name: []}
    }
    # Populate the facility ids
    with arcpy.da.SearchCursor(fl, [fl_id_field]) as cursor:
        for row in cursor:
            output["facilities"][fl_variable_name].append(str(row[0]))
    # populate the coverage dictionary with all demand areas (i)
    logging.getLogger().info("Initializing demand in output...")
    with arcpy.da.SearchCursor(dl, [dl_id_field, dl_demand_field, "SHAPE@AREA"]) as cursor:
        for row in cursor:
            output["demand"][str(row[0])] = {
                "area": round(row[2]),
                "demand": round(row[1]),
                "serviceableDemand": 0.0,
                "coverage": {fl_variable_name: {}}
            }
    # Dissolve all facility service areas so we can find the total serviceable area
    logging.getLogger().info("Combining facilities...")
    dissovled_geom = None
    with arcpy.da.SearchCursor(fl, ['SHAPE@']) as fcursor:
        for f in fcursor:
            if dissovled_geom is None:
                dissovled_geom = f[0]
            dissovled_geom = dissovled_geom.union(f[0])
    logging.getLogger().info("Determining partial coverage for each demand unit...")
    with arcpy.da.SearchCursor(dl, [dl_id_field, dl_demand_field, "SHAPE@"]) as dcursor:
        for d in dcursor:
            if not dissovled_geom.disjoint(d[2]):
                intersected = dissovled_geom.intersect(d[2], 4)
                if intersected.area > 0:
                    serviceable_demand = math.ceil(
                        float(intersected.area / d[2].area) * d[1])
                else:
                    serviceable_demand = 0.0
            else:
                serviceable_demand = 0.0
            # Make sure serviceable is less than or equal to demand, floating point issues
            if serviceable_demand < output["demand"][str(d[0])]["demand"]:
                output["demand"][str(d[0])]["serviceableDemand"] = serviceable_demand
            else:
                output["demand"][str(d[0])]["serviceableDemand"] = output["demand"][str(d[0])]["demand"]
            with arcpy.da.SearchCursor(fl, [fl_id_field, "SHAPE@"]) as fcursor:
                for f in fcursor:
                    if not d[2].disjoint(f[1]):
                        intersected_fd = d[2].intersect(f[1], 4)
                        if intersected_fd.area > 0:
                            demand = math.ceil(float(intersected_fd.area / d[2].area) * d[1])
                            if demand < output["demand"][str(d[0])]["serviceableDemand"]:
                                output["demand"][str(d[0])]["coverage"][fl_variable_name][str(f[0])] = demand
                            else:
                                output["demand"][str(d[0])]["coverage"][fl_variable_name][str(f[0])] = \
                                    output["demand"][str(d[0])]["serviceableDemand"]
    with arcpy.da.SearchCursor(dl, [dl_id_field, dl_demand_field, "SHAPE@AREA"]) as cursor:
        for row in cursor:
            output["totalServiceableDemand"] += output["demand"][str(row[0])]["serviceableDemand"]
            output["totalDemand"] += row[1]
    logging.getLogger().info("Partial coverage successfully generated.")
    reset_layers(dl, fl)
    return output

def generate_traumah_coverage(dl, dl_service_area, tc_layer, ad_layer, dl_demand_field, air_distance_threshold, dl_id_field="OBJECTID", tc_layer_id_field="OBJECTID", ad_layer_id_field="OBJECTID"):
    """
    Generates a coverage model for the TRAUMAH model. The traumah model uses trauma centers (TC), air depots (AD), and demand
    :param dl: (Feature Layer) The demand point layer
    :param dl_service_area (Feature Layer) The demand service area (generally derived from street network)
    :param tc_layer: (Feature Layer) The Trauma Center point layer
    :param ad_layer: (Feature Layer) The Air Depot point layer
    :param dl_demand_field: (string) The attribute that represents the demand in the demand layer
    :param air_distance_threshold: (float) The maximum total distance a helicopter can fly
    :param dl_id_field: (string) The attribute that represents unique ids for the demand layers
    :param tc_layer_id_field: (string) The attribute that represents unique ids for the trauma center layers
    :param ad_layer_id_field: (string) The attribute that represents unique ids for the air depot layers
    :return: (dictionary) A nested dictionary storing the coverage relationships
    """
    # Reset DF
    # Check parameters so we get useful exceptions and messages
    if arcpy.Describe(dl).shapeType != "Point":
        raise TypeError("Demand layer must have point geometry")
    if arcpy.Describe(dl_service_area).shapeType != "Polygon":
        raise TypeError("Demand layer must have polygon geometry")
    if arcpy.Describe(tc_layer).shapeType != "Point":
        raise TypeError("Trauma center layer must have point geometry")
    dl_field_names = [f.name for f in arcpy.Describe(dl).fields]
    dl_service_area_field_names = [f.name for f in arcpy.Describe(dl_service_area).fields]
    if dl_demand_field not in dl_field_names:
        raise ValueError("'{}' field not found in demand layer".format(dl_demand_field))
    if dl_id_field not in dl_field_names:
        raise ValueError("'{}' field not found in demand layer".format(dl_id_field))
    if dl_id_field not in dl_service_area_field_names:
        raise ValueError("'{}' field not found in demand service area layer".format(dl_id_field))
    tc_layer_field_names = [f.name for f in arcpy.Describe(tc_layer).fields]
    if tc_layer_id_field not in tc_layer_field_names:
        raise ValueError("'{}' field not found in trauma center layer".format(tc_layer_id_field))
    ad_layer_field_names = [f.name for f in arcpy.Describe(ad_layer).fields]
    if ad_layer_id_field not in ad_layer_field_names:
        raise ValueError("'{}' field not found in air depot layer".format(ad_layer_id_field))
    reset_layers(dl, dl_service_area, tc_layer, ad_layer)
    ad_variable_name = "AirDepot"
    tc_variable_name = "TraumaCenter"
    ad_tc_variable_name = "ADTCPair"

    logging.getLogger().info("Initializing facilities in output...")
    output = {
        "version": version.__version__,
        "type": {
            "mode": "coverage",
            "type": "traumah",
        },
        "demand": {},
        "totalDemand": 0.0,
        "totalServiceableDemand": 0.0,
        "facilities": {ad_variable_name: [],
                       tc_variable_name: []}
    }
    # Populate the facility ids
    with arcpy.da.SearchCursor(ad_layer, [ad_layer_id_field]) as cursor:
        for row in cursor:
            output["facilities"][ad_variable_name].append(str(row[0]))
    with arcpy.da.SearchCursor(tc_layer, [tc_layer_id_field]) as cursor:
        for row in cursor:
            output["facilities"][tc_variable_name].append(str(row[0]))
    # populate the coverage dictionary with all demand areas (i)
    logging.getLogger().info("Initializing demand in output...")
    with arcpy.da.SearchCursor(dl, [dl_id_field, dl_demand_field, "SHAPE@AREA"]) as cursor:
        for row in cursor:
            output["demand"][str(row[0])] = {
                "area": round(row[2]),
                "demand": round(row[1]),
                "serviceableDemand": 0.0,
                "coverage": {tc_variable_name: [],
                             ad_tc_variable_name: []
                }
            }
    logging.getLogger().info("Determining binary coverage (using ground transport service area) for each demand unit...")
    with arcpy.da.SearchCursor(tc_layer, [tc_layer_id_field, "SHAPE@"]) as fcursor:
        for f in fcursor:
            with arcpy.da.SearchCursor(dl_service_area, [dl_id_field, "SHAPE@"]) as dcursor:
                for d in dcursor:
                    if not f[1].disjoint(d[1]):
                        output["demand"][str(d[0])]["coverage"][tc_variable_name].append({
                            tc_variable_name: str(f[0])
                        })

    logging.getLogger().info("Determining binary coverage (using air transportation) for each demand unit...")
    with arcpy.da.SearchCursor(dl, [dl_id_field, "SHAPE@"]) as dcursor:
        for d in dcursor:
            distances = {}
            with arcpy.da.SearchCursor(tc_layer, [tc_layer_id_field, "SHAPE@"]) as tc_cursor:
                for tc in tc_cursor:
                    distances[tc[0]] = d[1].distanceTo(tc[1])

            with arcpy.da.SearchCursor(ad_layer, [ad_layer_id_field, "SHAPE@"]) as ad_cursor:
                for ad in ad_cursor:
                    distance = d[1].distanceTo(ad[1])
                    for k, v in distances.items():
                         if distance+v <= air_distance_threshold:
                             output["demand"][str(d[0])]["coverage"][ad_tc_variable_name].append({
                                 tc_variable_name: str(k),
                                 ad_variable_name: str(ad[0])
                             })
    logging.getLogger().info("Binary traumah coverage successfully generated.")
    reset_layers(dl, tc_layer, ad_layer)
    return output


def get_covered_demand(dl, dl_demand_field, mode, *args):
    """
    Finds to total coverage when facility layers are used
    Merges polygons & dissolves them to form one big area of total coverage
    Then intersects with demand layer. Only used for partial coverages

    Honors definition query and selection for facility layers
    :param dl: (Feature Layer) The demand polygon or point layer
    :param dl_demand_field: (string) The field representing demand
    :param mode: (string) ['binary', 'partial'] The method to use to evaluate coverage
    :param args: (Feature Layer) The facility layers to use
    :return: (dictionary) A dictionary of similar format to the coverage format
    """
    # Reset DF
    # Check parameters so we get useful exceptions and messages
    reset_layers(dl)
    if arcpy.Describe(dl).shapeType not in ["Polygon", "Point"]:
        raise TypeError("Demand layer must have polygon geometry")
    dl_field_names = [f.name for f in arcpy.Describe(dl).fields]
    if dl_demand_field not in dl_field_names:
        raise ValueError("'{}' field not found in demand layer".format(dl_demand_field))
    # Check that all facility layers are polygon
    for fl in args:
        if arcpy.Describe(fl).shapeType != "Polygon":
            raise TypeError("{} is not a polygon layer".format(fl.desc.name))
    if fl is None:
        raise ValueError("No facility service area feature layers specified")
    logging.getLogger().info("Combining facilities...")
    dissovled_geom = None
    for layer in args:
        with arcpy.da.SearchCursor(layer, ['SHAPE@']) as fcursor:
            for f in fcursor:
                if dissovled_geom is None:
                    dissovled_geom = f[0]
                dissovled_geom = dissovled_geom.union(f[0])
    total_coverage = 0
    logging.getLogger().info("Summing service coverage for each demand unit...")
    with arcpy.da.SearchCursor(dl, [dl_demand_field, "SHAPE@"]) as dcursor:
        if arcpy.Describe(dl).shapeType == "Polygon" and mode == "partial":
            for d in dcursor:
                if not dissovled_geom.disjoint(d[1]):
                    intersected = dissovled_geom.intersect(d[1], 4)
                    if intersected.area > 0:
                        serviceable_demand = math.ceil(
                            float(intersected.area / d[1].area) * d[0])
                    else:
                        serviceable_demand = 0.0
                else:
                    serviceable_demand = 0.0
                # Make sure serviceable is less than or equal to demand, floating point issues
                if serviceable_demand < d[0]:
                    total_coverage += serviceable_demand
                else:
                    total_coverage += d[0]
        else:  # binary point or polygon
            for d in dcursor:
                if dissovled_geom.contains(d[1]):  # check if valid
                    serviceable_demand = d[0]
                else:
                    serviceable_demand = 0.0
                total_coverage += serviceable_demand
    logging.getLogger().info("Covered demand is: {}".format(total_coverage))
    reset_layers(dl)
    return total_coverage
