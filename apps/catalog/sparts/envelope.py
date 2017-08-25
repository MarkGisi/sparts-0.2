"""
Copyright (c) 2017 Wind River Systems, Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at:

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software  distributed
under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES
OR CONDITIONS OF ANY KIND, either express or implied.

envelope routes
"""
import zipfile
import shutil
import datetime
import json
import os
import hashlib
import codecs
from urllib.parse import urlparse
from flask import render_template, request, abort, send_file, render_template_string, \
    redirect, url_for
from sqlalchemy import and_
from sqlalchemy.sql import exists
from werkzeug.utils import secure_filename
from sparts import app, db_session, render_page, jsonify, stacktrace
from sparts.models import Part, Supplier, Artifact, Envelope, BOM, BOMItem
from sparts.exceptions import EnvelopeError

def extract_and_parse_envelope(envelope_path, extract_path):
    """extract and parse the zip file at envelope_path and add it to the database and return the
    envelope instance
    """
    base_path = os.path.dirname(envelope_path)
    filename = os.path.basename(envelope_path)
    toc_path = os.path.join(extract_path, "_TOC.json")

    try:
        with zipfile.ZipFile(envelope_path) as envelope:
            envelope.extractall(extract_path)
    except:
        raise EnvelopeError("Failed to extract the zip file '" + str(filename) \
            + "'. The archive was corrupt.")

    # read the table of contents

    assert os.path.exists(toc_path), \
        "Invalid evelope. Missing required table of contentes file _TOC.json"

    toc = None
    envelope = Envelope()

    try:
        with open(toc_path, "r") as toc_file:
            toc = toc_file.read()
    except:
        raise EnvelopeError("Failed to read the table of contents file _TOC.json.")

    try:
        toc = json.loads(toc)
    except:
        raise EnvelopeError("Failed to parse JSON data in the table of contents.")

    assert "artifacts" in toc, \
        "Invalid JSON data in the table of contents, missing required field 'artifacts'."

    envelope.toc = json.dumps(toc)
    toc = toc["artifacts"]

    assert isinstance(toc, list), "Invalid JSON data in table of contents." \
        + " Expected a list of artifacts. Got <pre>" \
        + json.dumps(toc, indent=True) + "</pre>"

    for artifact in toc:
        for col in Artifact.__table__.columns:
            if col.key != "id" and col.nullable is False:
                assert col.key in artifact, "Invalid JSON data in the table of contents." \
                    + "The following artifact  was missing required field '" + col.key + "'." \
                    + "<br><br><pre>" + json.dumps(artifact, indent=True) + "</pre>" \
                    + "Note that field names are case sensitive and must appear " \
                    + "exactly as specified."
        #
        # the code below will throw an error if another artifact with this UUID already
        # existed. instead can link envelope to the existing artifact or overwrite old artifact.
        #

        assert not db_session.query(exists().where(Artifact.uuid == artifact["uuid"])).scalar(), \
            "Your envelope contained an artifact with UUID = '" + artifact["uuid"] \
            + "'. However, another artifact with that UUID already exists in the database. "\
            + "UUID's must be unique."

    # create a new envelope

    envelope.extract_dir = base_path

    # insert artifacts data in the envelope

    for artifact_dict in toc:
        artifact = Artifact()
        for col in Artifact.__table__.columns:
            if col.key in artifact_dict:
                setattr(artifact, col.key, artifact_dict[col.key])

        # if this is the envelope artifact, set the attributes of the envelope

        if artifact.content_type == "this":

            envelope.uuid = artifact.uuid
            envelope.short_id = artifact.short_id
            envelope.checksum = artifact.checksum
            envelope.openchain = artifact.openchain
            envelope.filename = artifact.filename
            envelope.label = artifact.label

            db_session.add(envelope)
            db_session.flush()

        # otherwise add it to the envelopes's list of artifacts

        else:

            try:
                parsed_uri = urlparse(artifact.uri)
            except:
                raise EnvelopeError("Failed to parse the URI '" + artifact.uri \
                 + "' for the following artifact. <br><pre>" \
                 + json.dumps(artifact_dict, indent=True) + "</pre>")

            assert parsed_uri.scheme != "", \
                "There was no scheme in the URI given for the following artifact <br><pre>" \
                + json.dumps(artifact_dict, indent=True) + "</pre>"

            if parsed_uri.scheme == "envelope":

                assert parsed_uri.netloc != "", "Missing net location for the URI given for " \
                    + " the following artifact <br><pre>" \
                    + json.dumps(artifact_dict, indent=True) + "</pre>"

                assert artifact.path != "" and artifact.path is not None, "Missing path for" \
                    + " the following artifact <br><pre>" \
                    + json.dumps(artifact_dict, indent=True) + "</pre>"

                assert artifact.path[0] == "/", "Invalid path in " \
                    + " the following artifact <br><pre>" \
                    + json.dumps(artifact_dict, indent=True) + "</pre>" \
                    + " <br> Paths must begin with a slash (/) symbol."

                if len(artifact.path) > 1:
                    assert artifact.path[-1] != "/", "Invalid path in " \
                        + " the following artifact <br><pre>" \
                        + json.dumps(artifact_dict, indent=True) + "</pre>" \
                        + "<br> Paths should not end with a slash."

                artifact_path = os.path.join(base_path, "envelope")
                artifact_path = os.path.join(artifact_path, parsed_uri.netloc)
                artifact_path = os.path.normpath(artifact_path + artifact.path)
                artifact_path = os.path.join(artifact_path, artifact.filename)

                assert os.path.exists(artifact_path), \
                    "The table of contents pointed to the artifact " \
                    + "<br><pre>" + json.dumps(artifact_dict, indent=True) \
                    + "</pre> <br> But it didn't exist in the envelope."

                with open(artifact_path, "rb") as artifact_file:
                    artifact_content = artifact_file.read()
                    artifact_checksum = hashlib.sha1(artifact_content).hexdigest()

                    #
                    # TODO: enable validating checksums
                    #

                    # assert artifact_checksum == artifact.checksum, "Invalid checksum for " \
                    #     + " the following artifact <br><pre>" \
                    #     + json.dumps(artifact_dict, indent=True) + "</pre>" \
                    #     + "<br> Expected '" + artifact_checksum + "', " \
                    #     + "got '" + artifact.checksum \
                    #     + "'. The files provided in this envelope might be corrupt."

                    artifact.checksum = artifact_checksum

                # copy the artifact to the artifacts folder

                shutil.copyfile(artifact_path, \
                    os.path.join(app.config["ARTIFACT_FOLDER"], artifact.checksum))

                # parse bill of materials

                if artifact.content_type == "oss_bom" and artifact.filename[-7:] == ".ossbom":

                    with open(artifact_path, "r") as bom_file:

                        try:
                            bom_data = json.loads(bom_file.read())

                        except:
                            raise EnvelopeError("Failed to parse the JSON in following " \
                                + "bill of materials artifact:" \
                                + "<br><br><pre>" + json.dumps(artifact_dict, indent=True) \
                                + "</pre><br>Please make sure the file '" \
                                + artifact.filename  + "' contains valid JSON data.")

                        bom = BOM()

                        for col in BOM.__table__.columns:
                            if col.key != "id" and not col.nullable:
                                assert col.key in bom_data, \
                                    "Invalid item in the following bill of materials artifact:" \
                                    + "<br><br><pre>" + json.dumps(artifact_dict, indent=True) \
                                    + "</pre><br>Missing required field '" + col.key + "'"

                            if col.key in bom_data and col.key != "items":
                                setattr(bom, col.key, bom_data[col.key])

                        assert "items" in bom_data, "Missing required field 'items'" \
                             + " in the following bill of materials artifact: <br><br><pre>" \
                             + json.dumps(artifact_dict, indent=True) + "</pre><br>"


                        for bom_item_dict in bom_data["items"]:

                            bom_item = BOMItem()

                            for col in BOMItem.__table__.columns:
                                if col.key != "id" and not col.nullable:
                                    assert col.key in bom_item_dict, \
                                        "Invalid JSON data in the following bill of materials" \
                                        + " artifact: <br><br><pre>" \
                                        + json.dumps(artifact_dict, indent=True) \
                                        + "</pre><br> The following entry was misising " \
                                        + "required field '" + col.key + "'. " + "<br><pre>" \
                                        + json.dumps(bom_item_dict, indent=True) \
                                        + "</pre><br>Note that field names are case sensitive " \
                                        + "and must appear exactly as specified."

                                if col.key in bom_item_dict:
                                    setattr(bom_item, col.key, bom_item_dict[col.key])

                            assert bom_item.path[0] == "/", "Invalid path in " \
                                + " the following BOM entry <br><pre>" \
                                + json.dumps(bom_item_dict, indent=True) + "</pre>" \
                                + " <br> Paths must begin with a slash (/) symbol."

                            if len(bom_item.path) > 1:
                                assert bom_item.path[-1] != "/", "Invalid path in " \
                                    + " the following BOM entry <br><pre>" \
                                    + json.dumps(bom_item_dict, indent=True) + "</pre>" \
                                    + "<br> Paths should not end with a slash."

                            bom.items.append(bom_item)

                        bom.artifact = artifact

                        db_session.add(bom)
                        db_session.flush()

                        envelope.boms.append(bom)
                        db_session.flush()

            envelope.artifacts.append(artifact)

    db_session.flush()
    db_session.commit()

    #
    # TODO: add envelope to the blockchain
    #

    return envelope


@app.route("/envelope/upload", methods=["POST"])
def upload_envelope():
    """route for uploading an envelope file"""
    response_data = {}

    # compute a unique, random extract path directory name baseed on time
    base_dirname = hashlib.sha1(codecs.encode(str(datetime.datetime.now()), "utf-8")).hexdigest()
    base_path = os.path.join(app.config["UPLOAD_FOLDER"], base_dirname)

    try:

        assert "envelope" in request.files, "Envelope file was not submitted"

        file = request.files["envelope"]

        assert file.filename != "", "No file was selected"

        filename = secure_filename(file.filename)

        file_path = os.path.join(base_path, filename)
        extract_path = os.path.join(base_path, "envelope")

        assert not os.path.exists(base_path), \
            "Could not create unique directory to extract envelope files." + \
            " Please try again later."

        try:
            os.makedirs(extract_path)
        except:
            raise EnvelopeError("Failed to create directory to extract envelope")

        file.save(file_path)

        # to ensure atomic operation on this file

        os.rename(file_path, file_path)

        assert "part_id" in request.args, "Invalid request, part_id was missing."

        part_query = db_session.query(Part).filter(Part.id == request.args["part_id"])

        assert part_query.count() == 1, "Part no longer existed in the database."

        part = part_query.one()

        envelope = extract_and_parse_envelope(file_path, extract_path)

        envelope.blockchain = part.blockchain
        part.envelope_id = envelope.id

        db_session.flush()
        db_session.commit()

        #remove zip file
        os.remove(file_path)

        response_data["successfully_uploaded"] = True
        response_data["envelope_html"] = render_template("envelope_table.html", envelope=envelope)

    except (AssertionError, EnvelopeError) as error:
        response_data["error_message"] = str(error)

    except:
        response_data["error_message"] = stacktrace()

    # delete the extracted files in case something went wrong

    if "error_message" in response_data:
        shutil.rmtree(base_path)

    return jsonify(response_data)


def find_envelope(uuid):
    """find the envelope with the given UUID and return the instance, otherwise return 404 page
    """
    envelope_query = db_session.query(Envelope).filter(Envelope.uuid == uuid)
    if envelope_query.count() != 1:
        abort(404)
    return envelope_query.one()


def delete_envelope(envelope):
    """delete envelope and all its associated artifacts, boms, and files
    """
    if envelope.boms:
        boms = envelope.boms[:]
        envelope.boms = []
        db_session.flush()

        for bom in boms:
            bomitems = bom.items[:]
            bom.items = []
            db_session.flush()

            for item in bomitems:
                db_session.delete(item)

            db_session.flush()
            db_session.delete(bom)
            db_session.flush()

    artifacts = envelope.artifacts[:]
    envelope.artifacts = []
    db_session.flush()

    for artifact in artifacts:
        db_session.delete(artifact)
        artifact_path = os.path.join(app.config["ARTIFACT_FOLDER"], artifact.checksum)
        if os.path.exists(artifact_path):
            os.remove(artifact_path)

    db_session.delete(envelope)
    db_session.flush()
    db_session.commit()

    shutil.rmtree(envelope.extract_dir)


@app.route("/envelope/delete/<uuid>", methods=["POST"])
def delete_envelope_by_uuid(uuid):
    """json route for deleting an envelope, expects envelope.uuid
    """
    try:
        data = request.json

        # check supplier password

        if not db_session.query(exists().where( \
            and_(Supplier.id == data["supplier_id"], \
            Supplier.password == data["password"]))).scalar():

            return jsonify({"failed": True, "invalid_password": True})

        # if there are any parts that have this envelope, delete their relationship

        for part, _ in db_session.query(Part, Envelope).join(Envelope) \
            .filter(Envelope.uuid == uuid).all():

            part.envelope = None
            db_session.flush()

        delete_envelope(find_envelope(uuid))
        return jsonify({"failed": False, \
            "envelope_html": render_template("envelope_table.html", envelope=None)})
    except:
        return jsonify({"failed": True, "error_message": stacktrace()})


@app.route("/envelope/download/<uuid>/<filename>")
def download_envelope(uuid, filename):
    """create viewers for envelope and bom, zip up the envelope and artifact files, and send it to
    the client
    """
    envelope = find_envelope(uuid)

    base_path = os.path.join(envelope.extract_dir, "envelope")
    viewer_path = os.path.join(base_path, "_viewer")
    resources_path = os.path.join(viewer_path, "resources")
    app_path = os.path.dirname(os.path.realpath(__file__))
    static_path = os.path.join(app_path, "static")
    templates_path = os.path.join(app_path, "templates")
    envelope_viewer_template = os.path.join(templates_path, "view_envelope.html")
    bom_viewer_template = os.path.join(templates_path, "view_bom.html")
    images_path = os.path.join(static_path, "images")
    envelope_html_file = os.path.join(viewer_path, "index.html")
    bom_html_file = os.path.join(viewer_path, "BOM.html")
    envelope_zip_file = os.path.join(envelope.extract_dir, filename)

    if envelope_zip_file[-4:] == ".zip":
        envelope_zip_file_noext = envelope_zip_file[:-4]
    else:
        envelope_zip_file_noext = envelope_zip_file

    if os.path.exists(envelope_zip_file):
        os.remove(envelope_zip_file)

    if not os.path.exists(resources_path):

        os.makedirs(resources_path)

        for image in ["folder.png", "folder-closed.png", "file.png", "notice-file.png", \
            "spdx-file-2.png", "openchain1-1.png", "blockchain-logo.png", "windriver.png", \
            "envelope.png", "bom.png", "crypto-file.png"]:

            shutil.copyfile(os.path.join(images_path, image), os.path.join(resources_path, image))


    with open(envelope_viewer_template, "r") as viewer_template_file:
        envelope_viewer_html = render_template_string(viewer_template_file.read(), \
            envelope=envelope, \
            artifact_graph=get_artifact_graph(envelope), \
            images_folder="resources/", \
            static_content_links=True)

        with open(envelope_html_file, "w") as envelope_file:
            envelope_file.write(envelope_viewer_html)

    with open(bom_viewer_template, "r") as bom_template_file:
        bom_viewer_html = render_template_string(bom_template_file.read(), \
            envelope=envelope, \
            bom_graphs=get_bom_graphs(envelope), \
            images_folder="resources/", \
            static_content_links=True)

        with open(bom_html_file, "w") as bom_file:
            bom_file.write(bom_viewer_html)

    shutil.make_archive(envelope_zip_file_noext, 'zip', base_path)

    return send_file(envelope_zip_file, os.path.basename(envelope_zip_file))

def get_artifact_graph(envelope):
    """create a recursive artifact graph"""

    def artifact_graph(artifact_paths):

        graph = {"dirname": "", "subdir": [], "content": []}

        path_roots = {}

        for path, artifact in artifact_paths:

            path_root = path.split("/")[1]

            if path_root not in path_roots:
                path_roots[path_root] = []

            next_level_dir = "/" +  "/".join(path.split("/")[2:])

            path_roots[path_root].append((next_level_dir, artifact))

        for root in path_roots:
            if root == "":
                for _, artifact in path_roots[root]:
                    graph["content"].append(artifact)
            else:

                branch = artifact_graph(path_roots[root])
                branch["dirname"] = root
                graph["subdir"].append(branch)

        return graph

    return [artifact_graph([(artifact.path, artifact) for artifact in envelope.artifacts])]


@app.route("/envelope/view/<uuid>")
def view_envelope(uuid):
    """page for viewing an envelope
    """
    envelope = find_envelope(uuid)

    return render_template("view_envelope.html", envelope=envelope, \
        artifact_graph=get_artifact_graph(envelope), \
        images_folder="/static/images", \
        static_content_links=False)


def get_artifact(uuid):
    """search database for an artifact with the given UUID and return its instance along with
    where the artifact file is saved"""
    artifact_query = db_session.query(Artifact).filter(and_(Artifact.uuid == uuid))
    if artifact_query.count() != 1:
        return None, None

    artifact = artifact_query.one()
    artifact_file = os.path.join(app.config["ARTIFACT_FOLDER"], artifact.checksum)

    if not os.path.exists(artifact_file):
        return None, None

    return artifact, artifact_file


@app.route("/artifact/<uuid>/<filename>")
def download_artifact_filename(uuid, filename):
    """download artifact by UUID and filename
    """
    artifact, artifact_file = get_artifact(uuid)

    if artifact is None:
        abort(404)

    # if the artifact is an html page, serve its contents

    if artifact.filename[-5:] == ".html" or artifact.filename[-4:] == ".htm":
        with open(artifact_file) as file:
            return render_template_string(file.read())

    # if this is a crypto file, display it with crypto viewer (unless it fails)

    # try:
    if artifact.content_type == "crypto":
        with open(artifact_file) as file:
            crypto = json.loads(file.read())
            assert float(crypto["crypto_spec_version"]) >= 2.0
            return render_page("crypto_viewer", \
                filelist=crypto["crypto_evidence"], artifact=artifact, \
                package_name=crypto["package_name"], \
                verif_code=crypto["file_collection_verification_code"])
    # except:
    #     pass

    return send_file(artifact_file, filename)


@app.route("/artifact/<uuid>")
def download_artifact(uuid):
    """download artifact by UUID
    """
    artifact, _ = get_artifact(uuid)
    return redirect(url_for("download_artifact_filename", uuid=uuid, filename=artifact.filename))


def get_bom_graphs(envelope):
    """create a recursive graph of bill of materials"""

    def bom_graph(bom_paths):

        graph = {"dirname": "", "subdir": [], "content": []}

        path_roots = {}

        for path, bom_item in bom_paths:

            path_root = path.split("/")[1]

            if path_root not in path_roots:
                path_roots[path_root] = []

            next_level_dir = "/" +  "/".join(path.split("/")[2:])

            path_roots[path_root].append((next_level_dir, bom_item))


        for root in path_roots:
            if root == "":
                for _, bom_item in path_roots[root]:

                    spdx_artifact = None
                    crypto_artifact = None

                    if bom_item.spdx:
                        artifact, _ = get_artifact(bom_item.spdx)
                        if artifact is not None:
                            spdx_artifact = artifact
                        else:
                            spdx_artifact = "Invalid"
                    if bom_item.crypto:
                        artifact, _ = get_artifact(bom_item.crypto)
                        if artifact is not None:
                            crypto_artifact = artifact
                        else:
                            crypto_artifact = "Invalid"

                    graph["content"].append((bom_item, spdx_artifact, crypto_artifact))
            else:

                branch = bom_graph(path_roots[root])
                branch["dirname"] = root
                graph["subdir"].append(branch)

        return graph

    def get_bom_graph(bom):
        return [bom_graph([(bom_item.path, bom_item) for bom_item in bom.items])]

    if envelope.boms:
        return [(bom, get_bom_graph(bom)) for bom in envelope.boms]
    else:
        return []


@app.route("/envelope/bom/view/<envelope_uuid>")
def view_envelope_bom(envelope_uuid):
    """envelope BOM viewer page"""

    envelope = find_envelope(envelope_uuid)

    return render_template("view_bom.html", \
        envelope=envelope, \
        bom_graphs=get_bom_graphs(envelope), \
        images_folder="/static/images", \
        static_content_links=False)


@app.route("/envelopes")
def all_envelopes():
    """page for viewing list of envelopes saved in the database. not implemented yet.
    """
    return render_page("envelopes", envelopes=db_session.query(Envelope))
