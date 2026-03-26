"""Tests for the KPI dashboard analysis.

Write at least 3 tests:
1. test_extraction_returns_dataframes — extract_data returns a dict of DataFrames
2. test_kpi_computation_returns_expected_keys — compute_kpis returns a dict with your 5 KPI names
3. test_statistical_test_returns_pvalue — run_statistical_tests returns results with p-values
"""
import pytest


def test_extraction_returns_dataframes():
    """Connect to the database, extract data, and verify the result is a dict of DataFrames."""
    # TODO: Call connect_db and extract_data, then assert the result is a dict
    #       with DataFrame values for each expected table
    pass


def test_kpi_computation_returns_expected_keys():
    """Compute KPIs and verify the result contains all expected KPI names."""
    # TODO: Extract data, call compute_kpis, then assert the returned dict
    #       contains the keys matching your 5 KPI names
    pass


def test_statistical_test_returns_pvalue():
    """Run statistical tests and verify results include p-values."""
    # TODO: Extract data, call run_statistical_tests, then assert at least
    #       one result contains a numeric p-value between 0 and 1
    pass
