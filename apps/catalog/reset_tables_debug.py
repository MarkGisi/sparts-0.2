"""
Copyright (c) 2017 Wind River Systems, Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at:

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software  distributed
under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES
OR CONDITIONS OF ANY KIND, either express or implied.
"""
from sparts.database import init_db, engine, db_session
from sparts.models import Part, Supplier, Category, Artifact, Envelope, envelope_artifacts, \
    envelope_boms, part_categories, BOM, BOMItem

tables = [envelope_boms, BOMItem.__table__, BOM.__table__, envelope_artifacts, part_categories, \
    Part.__table__, Envelope.__table__, Artifact.__table__, Category.__table__, Supplier.__table__]

for table in tables:
    try:
        table.drop(engine)
    except:
        pass

init_db()

s = Supplier()
s.name = "Test"
s.password = "202cb962ac59075b964b07152d234b70"
s.blockchain = False

db_session.add(s)

db_session.flush()

c = Category()
c.name = "operating-systems"
c.uuid = "123"
c.description = "Operating Systems"
db_session.add(c)
db_session.flush()

c2 = Category()
c2.name = "containers"
c2.uuid = "7686"
c2.description = "Containers"
db_session.add(c2)
db_session.flush()

c3 = Category()
c3.name = "libraries"
c3.uuid = "7682316"
c3.description = "Libraries"
db_session.add(c3)
db_session.flush()

c4 = Category()
c4.name = "drivers"
c4.uuid = "768232316"
c4.description = "Drivers & Firmware"
db_session.add(c4)
db_session.flush()

p = Part()

p.usku = "4564654-564-574"
p.name = "Test part"
p.version = "3.2"
p.licensing = "GPL"
p.supplier_id = s.id
p.categories.append(c)
p.supplier_part_id = "3252"
p.status = ""
p.url = ""
p.description = ""

db_session.add(p)
db_session.flush()

p2 = Part()

p2.usku = "4564342654-564-574"
p2.name = "Mixed part"
p2.version = "1.2"
p2.licensing = "MIT"
p2.supplier_id = s.id
p2.categories.append(c)
p2.categories.append(c2)
p2.supplier_part_id = "141"
p2.status = ""
p2.url = ""
p2.description = ""

db_session.add(p2)
db_session.flush()

p3 = Part()

p3.usku = "456433242654-564-574"
p3.name = "Part with no category"
p3.version = "1.2"
p3.licensing = "MIT"
p3.supplier_id = s.id
p3.supplier_part_id = "141"
p3.status = ""
p3.url = ""
p3.description = ""

db_session.add(p3)
db_session.flush()

db_session.commit()
