"""
Copyright (c) 2017 Wind River Systems, Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at:

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software  distributed
under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES
OR CONDITIONS OF ANY KIND, either express or implied.

data models
"""
from sqlalchemy import Table, Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sparts.database import Base
from sparts.api import get_uuid, save_supplier_to_blockchain, \
    save_part_to_blockchain, save_envelope_to_blockchain, save_category_to_blockchain

class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True)
    uuid = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False)
    password = Column(String, nullable=False)
    blockchain = Column(Boolean, nullable=False)
    url = Column(String)
    parts = relationship("Part")

    def __init__(self):
        self.uuid = get_uuid()

    def save_to_blockchain(self):
        save_supplier_to_blockchain(self)


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    uuid = Column(String, nullable=False, unique=True)
    description = Column(String, nullable=False)

    def save_to_blockchain(self):
        save_category_to_blockchain(self)


class Artifact(Base):
    __tablename__ = "artifacts"

    id = Column(Integer, primary_key=True)
    uuid = Column(String, nullable=False, unique=True)
    short_id = Column(String)
    checksum = Column(String)
    filename = Column(String)
    content_type = Column(String)
    uri = Column(String)
    path = Column(String)
    label = Column(String)
    openchain = Column(Boolean)
    blockchain = Column(Boolean)


class BOM(Base):
    __tablename__ = "boms"

    id = Column(Integer, primary_key=True)
    artifact_id = Column(Integer, ForeignKey(Artifact.id))
    artifact = relationship("Artifact")
    items = relationship("BOMItem")
    name = Column(String, nullable=False)
    uuid = Column(String)
    part_uuid = Column(String)
    supplier = Column(String)
    label = Column(String)
    version = Column(String)
    description = Column(String)


class BOMItem(Base):
    __tablename__ = "bomitems"

    id = Column(Integer, primary_key=True)
    bom_id = Column(Integer, ForeignKey(BOM.id))
    name = Column(String, nullable=False)
    path = Column(String, nullable=False)
    top_license = Column(String, nullable=False)
    version = Column(String)
    checksum = Column(String)
    filename = Column(String)
    src_uri = Column(String)
    spdx = Column(String)
    crypto = Column(String)


envelope_boms = Table('envelope_boms', Base.metadata, \
        Column('envelope_id', Integer, ForeignKey("envelopes.id")), \
        Column('bom_id', Integer, ForeignKey("boms.id")) \
    )


envelope_artifacts = Table('envelope_artifacts', Base.metadata, \
        Column('envelope_id', Integer, ForeignKey("envelopes.id")), \
        Column('artifact_id', Integer, ForeignKey("artifacts.id")) \
    )

part_categories = Table('part_categories', Base.metadata, \
        Column('part_id', Integer, ForeignKey("parts.id")), \
        Column('category_uuid', String, ForeignKey("categories.uuid")) \
    )


class Envelope(Base):
    __tablename__ = "envelopes"

    id = Column(Integer, primary_key=True)
    uuid = Column(String, nullable=False, unique=True)
    short_id = Column(String, nullable=False, unique=True)
    checksum = Column(String)
    filename = Column(String)
    openchain = Column(Boolean)
    extract_dir = Column(String)
    label = Column(String)
    toc = Column(String)
    blockchain = Column(Boolean)
    artifacts = relationship("Artifact", secondary=envelope_artifacts)
    boms = relationship("BOM", secondary=envelope_boms)

    def save_to_blockchain(self):
        save_envelope_to_blockchain(self)


class Part(Base):
    __tablename__ = "parts"

    id = Column(Integer, primary_key=True)
    supplier_id = Column(Integer, ForeignKey(Supplier.id))
    envelope_id = Column(Integer, ForeignKey(Envelope.id))
    supplier = relationship("Supplier")
    envelope = relationship("Envelope")
    categories = relationship("Category", secondary=part_categories)

    uuid = Column(String, nullable=False, unique=True)
    usku = Column(String, unique=True)
    supplier_part_id = Column(String, nullable=False)

    name = Column(String, nullable=False)
    version = Column(String, nullable=False)
    licensing = Column(String, nullable=False)

    url = Column(String)
    status = Column(String)
    description = Column(String)
    blockchain = Column(Boolean)

    checksum = Column(String)
    src_uri = Column(String)

    def __init__(self):
        self.uuid = get_uuid()

    def save_to_blockchain(self):
        save_part_to_blockchain(self)
