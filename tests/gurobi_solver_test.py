import json
import pulp
import unittest

from pyspatialopt.models import covering, utilities


class GUROBISolverTest(unittest.TestCase):
    def setUp(self):
        # Read the coverages
        with open("valid_coverages/partial_coverage1.json", "r") as f:
            self.partial_coverage = json.load(f)
        with open("valid_coverages/binary_coverage_polygon1.json", "r") as f:
            self.binary_coverage_polygon = json.load(f)
        with open("valid_coverages/binary_coverage_point1.json", "r") as f:
            self.binary_coverage_point = json.load(f)

        with open("valid_coverages/partial_coverage2.json", "r") as f:
            self.partial_coverage2 = json.load(f)
        with open("valid_coverages/binary_coverage_polygon2.json", "r") as f:
            self.binary_coverage_polygon2 = json.load(f)
        with open("valid_coverages/binary_coverage_point2.json", "r") as f:
            self.binary_coverage_point2 = json.load(f)

        with open("valid_coverages/serviceable_demand_polygon.json", "r") as f:
            self.serviceable_demand_polygon = json.load(f)
        with open("valid_coverages/serviceable_demand_point.json", "r") as f:
            self.serviceable_demand_point = json.load(f)

    def test_mclp(self):
        mclp = covering.create_mclp_model(self.binary_coverage_polygon, {"total": 5}, "mclp.lp")
        mclp.solve(pulp.GUROBI())
        ids = utilities.get_ids(mclp, "facility_service_areas")
        self.assertEqual(['1', '4', '5', '6', '7'], ids)

    def test_mclpcc(self):
        mclpcc = covering.create_mclp_cc_model(self.partial_coverage, {"total": 5}, "mclpcc.lp")
        mclpcc.solve(pulp.GUROBI())
        ids = utilities.get_ids(mclpcc, "facility_service_areas")
        self.assertEqual(['1', '4', '5', '6', '7'], ids)

    def test_threshold(self):
        threshold = covering.create_threshold_model(self.binary_coverage_point2, 30, "threshold.lp")
        threshold.solve(pulp.GUROBI())
        ids = utilities.get_ids(threshold, "facility2_service_areas")
        self.assertEqual(['10', '20', '4'], ids)

    def test_cc_threshold(self):
        ccthreshold = covering.create_cc_threshold_model(self.partial_coverage2, 80, "ccthreshold.lp")
        ccthreshold.solve(pulp.GUROBI())
        ids = utilities.get_ids(ccthreshold, "facility2_service_areas")
        self.assertEqual(['1', '10', '11', '13', '15', '17', '19', '20', '21', '22', '3', '4', '7', '9'], ids)

    def test_backup(self):
        merged_dict = covering.merge_coverages([self.binary_coverage_point, self.binary_coverage_point2])
        merged_dict = covering.update_serviceable_demand(merged_dict, self.serviceable_demand_point)
        bclp = covering.create_backup_model(merged_dict, {"total": 30}, "backup.lp")
        bclp.solve(pulp.GUROBI())
        ids = utilities.get_ids(bclp, "facility_service_areas")
        ids2 = utilities.get_ids(bclp, "facility2_service_areas")
        self.assertEqual(['1', '3', '4', '5', '6', '7'], ids)
        self.assertEqual(
            ['0', '1', '10', '12', '13', '14', '15', '16', '17', '18', '19', '2', '20', '22', '3', '4', '5', '6', '8',
             '9'], ids2)

    def test_lscp(self):
        merged_dict = covering.merge_coverages([self.binary_coverage_point, self.binary_coverage_point2])
        merged_dict = covering.update_serviceable_demand(merged_dict, self.serviceable_demand_point)
        lscp = covering.create_lscp_model(merged_dict, "lscp.lp")
        lscp.solve(pulp.GUROBI())
        ids = utilities.get_ids(lscp, "facility_service_areas")
        ids2 = utilities.get_ids(lscp, "facility2_service_areas")
        self.assertEqual(['1', '3', '4', '5', '6', '7'], ids)
        self.assertEqual(
            ['0', '1', '11', '12', '13', '14', '15', '16', '17', '19', '2', '20', '22', '4', '5', '6', '7', '9'], ids2)


if __name__ == '__main__':
    unittest.main()
