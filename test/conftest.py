# Copyright 2017 Palantir Technologies, Inc.
""" py.test configuration"""
import logging

LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s.%(funcName)s:%(lineno)d %(message)s"
logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT)


pytest_plugins = [
    'test.fixtures'
]
