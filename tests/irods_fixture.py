# -*- coding: utf-8 -*-
#
# Copyright © 2020, 2021 Genome Research Ltd. All rights reserved.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# @author Keith James <kdj@sanger.ac.uk>

from pathlib import PurePath

import pytest

from partisan.irods import (
    AVU,
    Baton,
    Collection,
)
from partisan.icommands import have_admin, imkdir, iput, irm, mkgroup, rmgroup
from partisan.metadata import ONTMetadata

tests_have_admin = pytest.mark.skipif(
    not have_admin(), reason="tests do not have iRODS admin access"
)

TEST_GROUPS = ["ss_study_01", "ss_study_02", "ss_study_03"]


def add_test_groups():
    if have_admin():
        for g in TEST_GROUPS:
            mkgroup(g)


def remove_test_groups():
    if have_admin():
        for g in TEST_GROUPS:
            rmgroup(g)


def add_rods_path(root_path: PurePath, tmp_path: PurePath) -> PurePath:
    parts = PurePath(*tmp_path.parts[1:])
    rods_path = root_path / parts
    imkdir(rods_path, make_parents=True)

    return rods_path


@pytest.fixture(scope="function")
def simple_collection(tmp_path):
    """A fixture providing an empty collection"""
    root_path = PurePath("/testZone/home/irods/test")
    coll_path = add_rods_path(root_path, tmp_path)

    try:
        yield coll_path
    finally:
        irm(root_path, force=True, recurse=True)


@pytest.fixture(scope="function")
def simple_data_object(tmp_path):
    """A fixture providing a collection containing a single data object containing
    UTF-8 data."""
    root_path = PurePath("/testZone/home/irods/test")
    rods_path = add_rods_path(root_path, tmp_path)

    obj_path = rods_path / "lorem.txt"
    iput("./tests/data/simple/data_object/lorem.txt", obj_path)

    try:
        yield obj_path
    finally:
        irm(root_path, force=True, recurse=True)


@pytest.fixture(scope="function")
def ont_gridion(tmp_path):
    """A fixture providing a set of files based on output from an ONT GridION
    instrument. This dataset provides an example of file and directory naming
    conventions. The file contents are dummy values."""
    root_path = PurePath("/testZone/home/irods/test")
    rods_path = add_rods_path(root_path, tmp_path)

    iput("./tests/data/ont/gridion", rods_path, recurse=True)
    expt_root = rods_path / "gridion"

    try:
        add_test_groups()

        yield expt_root
    finally:
        irm(root_path, force=True, recurse=True)
        remove_test_groups()


@pytest.fixture(scope="function")
def ont_synthetic(tmp_path, baton_session):
    root_path = PurePath("/testZone/home/irods/test")
    rods_path = add_rods_path(root_path, tmp_path)

    iput("./tests/data/ont/synthetic", rods_path, recurse=True)
    expt_root = PurePath(rods_path, "synthetic")

    avus = [
        avu.with_namespace(ONTMetadata.namespace)
        for avu in [
            AVU(ONTMetadata.EXPERIMENT_NAME.value, "simple_experiment_001"),
            AVU(ONTMetadata.INSTRUMENT_SLOT.value, "1"),
        ]
    ]

    Collection(
        baton_session,
        PurePath(
            expt_root,
            "simple_experiment_001",
            "20190904_1514_GA10000_flowcell011_69126024",
        ),
    ).meta_add(*avus)

    avus = [
        avu.with_namespace(ONTMetadata.namespace)
        for avu in [
            AVU(ONTMetadata.EXPERIMENT_NAME.value, "multiplexed_experiment_001"),
            AVU(ONTMetadata.INSTRUMENT_SLOT.value, "1"),
        ]
    ]

    Collection(
        baton_session,
        PurePath(
            expt_root,
            "multiplexed_experiment_001",
            "20190904_1514_GA10000_flowcell101_cf751ba1",
        ),
    ).meta_add(*avus)

    try:
        add_test_groups()

        yield expt_root
    finally:
        irm(root_path, force=True, recurse=True)
        remove_test_groups()


@pytest.fixture(scope="function")
def baton_session():
    client = Baton()
    client.start()

    try:
        yield client
    finally:
        client.stop()