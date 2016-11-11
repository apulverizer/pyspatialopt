# -*- coding: UTF-8 -*-
import logging
import math
import os
import qgis
import qgis.core
import qgis.utils
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
        layer.setSubsetString("")
        layer.removeSelection()


def generate_serviceable_demand(dl, dl_demand_field, dl_id_field, *args):
    """
    Finds to total serviceable coverage when 2 facility layers are used
    Merges polygons & dissolves them to form one big area of total coverage
    Then intersects with demand layer
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
    # Check parameters so we get useful exceptions and messages
    if dl.wkbType() not in [qgis.utils.QGis.WKBPoint, qgis.utils.QGis.WKBPolygon]:
        raise TypeError("Demand layer must have polygon or point geometry")
    dl_field_names = [field.name() for field in dl.pendingFields()]
    if dl_demand_field not in dl_field_names:
        raise ValueError("'{}' field not found in demand layer".format(dl_demand_field))
    if dl_id_field not in dl_field_names:
        raise ValueError("'{}' field not found in demand layer".format(dl_id_field))
    logging.getLogger().info("Initializing output...")
    if dl.wkbType() == qgis.utils.QGis.WKBPolygon:
        output = {
            "version": version.__version__,
            "demand": {},
            "type": {
                "mode": "serviceableDemand",
                "type": "partial"}
        }
    else:
        output = {
            "version": version.__version__,
            "demand": {},
            "type": {
                "mode": "serviceableDemand",
                "type": "binary"}
        }

    # Merge all of facility layers together
    logging.getLogger().info("Combining facilities...")
    dissolved_geom = None
    for layer in args:
        for feature in layer.getFeatures():
            if dissolved_geom is None:
                dissolved_geom = feature.geometry()
            dissolved_geom = dissolved_geom.combine(feature.geometry())
    logging.getLogger().info("Determining possible service coverage for each demand unit...")
    for feature in dl.getFeatures():
        if dl.wkbType() == qgis.utils.QGis.WKBPolygon:
            if dissolved_geom.intersects(feature.geometry()):
                intersected = dissolved_geom.intersection(feature.geometry())
                if intersected.area() > 0:
                    serviceable_demand = math.ceil(float(intersected.area() / feature.geometry().area()) * feature[
                        dl_demand_field])
                else:
                    serviceable_demand = 0.0
            else:
                serviceable_demand = feature[dl_demand_field]
        else:
            if dissolved_geom.contains(feature.geometry()):
                serviceable_demand = feature[dl_demand_field]
            else:
                serviceable_demand = 0.0
        # Make sure serviceable is less than or equal to demand, floating point issues
        output["demand"][str(feature[dl_id_field])] = {"serviceableDemand": 0}
        if serviceable_demand < feature[dl_demand_field]:
            output["demand"][str(feature[dl_id_field])]["serviceableDemand"] = serviceable_demand
        else:
            output["demand"][str(feature[dl_id_field])]["serviceableDemand"] = feature[dl_demand_field]
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
    if dl.wkbType() not in [qgis.utils.QGis.WKBPoint, qgis.utils.QGis.WKBPolygon]:
        raise TypeError("Demand layer must have polygon or point geometry")
    if fl.wkbType() != qgis.utils.QGis.WKBPolygon:
        raise TypeError("Facility service area layer must have polygon geometry")
    dl_field_names = [field.name() for field in dl.pendingFields()]
    if dl_demand_field not in dl_field_names:
        raise ValueError("'{}' field not found in demand layer".format(dl_demand_field))
    if dl_id_field not in dl_field_names:
        raise ValueError("'{}' field not found in demand layer".format(dl_id_field))
    fl_field_names = [field.name() for field in fl.pendingFields()]
    if fl_id_field not in fl_field_names:
        raise ValueError("'{}' field not found in facility service area layer".format(fl_id_field))
    reset_layers(dl, fl)
    if fl_variable_name is None:
        fl_variable_name = os.path.basename(os.path.abspath(fl.dataProvider().dataSourceUri())).split(".")[0]
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
    logging.getLogger().info("Initializing facilities in output...")
    for feature in fl.getFeatures():
        output["facilities"][fl_variable_name].append(str(feature[fl_id_field]))
    # Build empty data structure
    logging.getLogger().info("Initializing demand in output...")
    for feature in dl.getFeatures():
        output["demand"][str(feature[dl_id_field])] = {
            "area": None,
            "demand": round(feature[dl_demand_field]),
            "serviceableDemand": 0,
            "coverage": {fl_variable_name: {}}
        }
    logging.getLogger().info("Determining binary coverage for each demand unit...")
    for feature in fl.getFeatures():
        if dl.wkbType() == qgis.utils.QGis.WKBPoint:
            geom = feature.geometry()
            for dl_p in dl.getFeatures():
                geom2 = dl_p.geometry()
                if geom.intersects(geom2):
                    output["demand"][str(dl_p[dl_id_field])]["serviceableDemand"] = \
                        output["demand"][str(dl_p[dl_id_field])]["demand"]
                    output["demand"][str(dl_p[dl_id_field])]["coverage"][fl_variable_name][
                        str(feature[fl_id_field])] = 1
        else:
            geom = feature.geometry()
            for dl_p in dl.getFeatures():
                geom2 = dl_p.geometry()
                if geom.contains(geom2):
                    output["demand"][str(dl_p[dl_id_field])]["serviceableDemand"] = \
                        output["demand"][str(dl_p[dl_id_field])]["demand"]
                    output["demand"][str(dl_p[dl_id_field])]["coverage"][fl_variable_name][
                        str(feature[fl_id_field])] = 1
    for feature in dl.getFeatures():
        output["totalServiceableDemand"] += output["demand"][str(feature[dl_id_field])]["serviceableDemand"]
        output["totalDemand"] += feature[dl_demand_field]
    logging.getLogger().info("Binary coverage successfully generated.")
    reset_layers(dl, fl)
    return output


def generate_partial_coverage(dl, fl, dl_demand_field, dl_id_field, fl_id_field, fl_variable_name=None):
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
    if dl.wkbType() != qgis.utils.QGis.WKBPolygon:
        raise TypeError("Demand layer must have polygon geometry")
    if fl.wkbType() != qgis.utils.QGis.WKBPolygon:
        raise TypeError("Facility service area layer must have polygon geometry")
    dl_field_names = [field.name() for field in dl.pendingFields()]
    if dl_demand_field not in dl_field_names:
        raise ValueError("'{}' field not found in demand layer".format(dl_demand_field))
    if dl_id_field not in dl_field_names:
        raise ValueError("'{}' field not found in demand layer".format(dl_id_field))
    fl_field_names = [field.name() for field in fl.pendingFields()]
    if fl_id_field not in fl_field_names:
        raise ValueError("'{}' field not found in facility service area layer".format(fl_id_field))
    reset_layers(dl, fl)
    # If no facility layer name provided, use the name of the feature class/shapefile
    if fl_variable_name is None:
        fl_variable_name = os.path.basename(os.path.abspath(fl.dataProvider().dataSourceUri())).split(".")[0]
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
    # List all of the facilities
    for feature in fl.getFeatures():
        output["facilities"][fl_variable_name].append(str(feature[fl_id_field]))
    # Build empty data structure
    logging.getLogger().info("Initializing demand in output...")
    for feature in dl.getFeatures():
        output["demand"][str(feature[dl_id_field])] = {
            "area": round(feature.geometry().area()),
            "demand": round(feature[dl_demand_field]),
            "serviceableDemand": 0,
            "coverage": {fl_variable_name: {}}
        }
    # Dissolve all facility service areas so we can find the total serviceable area
    logging.getLogger().info("Combining facilities...")
    dissolved_geom = None
    for feature in fl.getFeatures():
        if dissolved_geom is None:
            dissolved_geom = feature.geometry()
        dissolved_geom = dissolved_geom.combine(feature.geometry())
    # Iterate over each intersected polygon and areal interpolate the demand that is covered
    logging.getLogger().info("Determining partial coverage for each demand unit...")
    for feature in dl.getFeatures():
        intersected = dissolved_geom.intersection(feature.geometry())
        if intersected.area() > 0:
            serviceable_demand = math.ceil(float(intersected.area() / feature.geometry().area()) * feature[dl_demand_field])
        else:
            serviceable_demand = 0.0
        # Make sure serviceable is less than or equal to demand, floating point issues
        if serviceable_demand < output["demand"][str(feature[dl_id_field])]["demand"]:
            output["demand"][str(feature[dl_id_field])]["serviceableDemand"] = serviceable_demand
        else:
            output["demand"][str(feature[dl_id_field])]["serviceableDemand"] = \
            output["demand"][str(feature[dl_id_field])]["demand"]

        for feature2 in fl.getFeatures():
            intersected_fd = feature.geometry().intersection(feature2.geometry())
            if intersected_fd.area() > 0:
                demand = math.ceil(float(intersected_fd.area() / feature.geometry().area()) * feature[dl_demand_field])
                if demand < output["demand"][feature[str(dl_id_field)]]["serviceableDemand"]:
                    output["demand"][str(feature[dl_id_field])]["coverage"][fl_variable_name] \
                        [str(feature2[fl_id_field])] = demand
                else:
                    output["demand"][str(feature[dl_id_field])]["coverage"][fl_variable_name][
                        str(feature2[fl_id_field])] = output["demand"][str(feature[dl_id_field])]["serviceableDemand"]
    for feature in dl.getFeatures():
        output["totalServiceableDemand"] += output["demand"][str(feature[dl_id_field])]["serviceableDemand"]
        output["totalDemand"] += feature[dl_demand_field]
    logging.getLogger().info("Partial coverage successfully generated.")
    reset_layers(dl, fl)
    return output


def get_covered_demand(dl, dl_demand_field, mode, *args):
    """
    Finds to total serviceable coverage when 2 facility layers are used
    Merges polygons & dissolves them to form one big area of total coverage
    Then intersects with demand layer
    :param dl: (Feature Layer) The demand polygon or point layer
    :param dl_demand_field: (string) The field representing demand
    :param mode: (string) ['binary', 'partial'] The type of coverage to use
    :param args: (Feature Layer) The facility layers to use
    :return: (dictionary) A dictionary of similar format to the coverage format
    """
    # Reset DF
    # Check parameters so we get useful exceptions and messages
    reset_layers(dl)
    # Check parameters so we get useful exceptions and messages
    if mode not in ['binary', 'partial']:
        raise ValueError("'{}' is not a valid mode").format(mode)
    if dl.wkbType() not in [qgis.utils.QGis.WKBPoint, qgis.utils.QGis.WKBPolygon]:
        raise TypeError("Demand layer must have polygon or point geometry")
    dl_field_names = [field.name() for field in dl.pendingFields()]
    if dl_demand_field not in dl_field_names:
        raise ValueError("'{}' field not found in demand layer".format(dl_demand_field))
        # Merge all of facility layers together
    logging.getLogger().info("Combining facilities...")
    dissolved_geom = None
    for layer in args:
        for feature in layer.getFeatures():
            if dissolved_geom is None:
                dissolved_geom = feature.geometry()
            dissolved_geom = dissolved_geom.combine(feature.geometry())
    total_coverage = 0
    logging.getLogger().info("Determining possible service coverage for each demand unit...")
    for feature in dl.getFeatures():
        if dl.wkbType() == qgis.utils.QGis.WKBPolygon and mode == "partial":
            if dissolved_geom.intersects(feature.geometry()):
                intersected = dissolved_geom.intersection(feature.geometry())
                if intersected.area() > 0:
                    serviceable_demand = float(intersected.area() / feature.geometry().area()) * feature[
                        dl_demand_field]
                else:
                    serviceable_demand = 0.0
            else:
                serviceable_demand = feature[dl_demand_field]
        else:
            if dissolved_geom.contains(feature.geometry()):
                serviceable_demand = feature[dl_demand_field]
            else:
                serviceable_demand = 0.0
        # Make sure serviceable is less than or equal to demand, floating point issues
        if serviceable_demand < feature[dl_demand_field]:
            total_coverage += serviceable_demand
        else:
            total_coverage += feature[dl_demand_field]
    logging.getLogger().info("Covered demand is: {}".format(total_coverage))
    reset_layers(dl)
    return total_coverage
