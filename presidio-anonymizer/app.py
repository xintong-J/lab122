"""REST API server for anonymizer."""

import json
import logging
import os
from collections import OrderedDict
from logging.config import fileConfig
from pathlib import Path

from flask import Flask, Response, jsonify, request
from presidio_anonymizer import AnonymizerEngine, DeanonymizeEngine
from presidio_anonymizer.entities import InvalidParamError
from presidio_anonymizer.operators import GenZ
from presidio_anonymizer.services.app_entities_convertor import AppEntitiesConvertor
from werkzeug.exceptions import BadRequest, HTTPException

DEFAULT_PORT = "3000"

LOGGING_CONF_FILE = "logging.ini"

WELCOME_MESSAGE = r"""
 _______  _______  _______  _______ _________ ______  _________ _______
(  ____ )(  ____ )(  ____ \(  ____ \\__   __/(  __  \ \__   __/(  ___  )
| (    )|| (    )|| (    \/| (    \/   ) (   | (  \  )   ) (   | (   ) |
| (____)|| (____)|| (__    | (_____    | |   | |   ) |   | |   | |   | |
|  _____)|     __)|  __)   (_____  )   | |   | |   | |   | |   | |   | |
| (      | (\ (   | (            ) |   | |   | |   ) |   | |   | |   | |
| )      | ) \ \__| (____/\/\____) |___) (___| (__/  )___) (___| (___) |
|/       |/   \__/(_______/\_______)\_______/(______/ \_______/(_______)
"""


class Server:
    """Flask server for anonymizer."""

    def __init__(self):
        fileConfig(Path(Path(__file__).parent, LOGGING_CONF_FILE))
        self.logger = logging.getLogger("presidio-anonymizer")
        self.logger.setLevel(os.environ.get("LOG_LEVEL", self.logger.level))
        self.app = Flask(__name__)
        self.logger.info("Starting anonymizer engine")
        self.anonymizer = AnonymizerEngine()
        self.deanonymize = DeanonymizeEngine()
        self.logger.info(WELCOME_MESSAGE)

        @self.app.route("/health")
        def health() -> str:
            """Return basic health probe result."""
            return "Presidio Anonymizer service is up"

        @self.app.route("/anonymize", methods=["POST"])
        def anonymize() -> Response:
            content = request.get_json()
            if not content:
                raise BadRequest("Invalid request json")

            anonymizers_config = AppEntitiesConvertor.operators_config_from_json(
                content.get("anonymizers")
            )
            if AppEntitiesConvertor.check_custom_operator(anonymizers_config):
                raise BadRequest("Custom type anonymizer is not supported")

            analyzer_results = AppEntitiesConvertor.analyzer_results_from_json(
                content.get("analyzer_results")
            )
            anoymizer_result = self.anonymizer.anonymize(
                text=content.get("text", ""),
                analyzer_results=analyzer_results,
                operators=anonymizers_config,
            )
            return Response(anoymizer_result.to_json(), mimetype="application/json")
        @self.app.route("/genz-preview", methods=["GET"])
        def genz_preview():
            """Return genz preview anonymization."""
            responsea = OrderedDict([
                ("example","Call Emily at 577-988-1234"),
                ("example output","Call GOAT at vibe check"),
                ("description","Example output of genz anonymizer.")
            ])
            responseb = json.dumps(responsea)
            return Response(responseb, mimetype='application/json')
        @self.app.route("/genz", methods=["GET"])
        def genz():
            """Return genz anonymization."""
            GEN_REQ = """{"text": "Please contact Emily Carter at 734-555-9284 if "
                "you have questions about the workshop registration.",
                "analyzer_results": [{"start": 15,
                "end": 27,
                "score": 0.3,
                "entity_type": "PERSON"},
                {"start": 31,
                "end": 43,
                "score": 0.95,
                "entity_type": "PHONE_NUMBER"}]
                }"""
            gz = GenZ()
            p_r = gz.operate(params={"entity_type": "PERSON"})
            ph_r = gz.operate(params={"entity_type": "PHONE_NUMBER"})
            text_e = f"Please contact {p_r} at {ph_r} if you have questions "\
                "about the workshop registration."
            p_s = 15
            p_e = p_s + len(p_r)
            ph_s = p_e + 4
            ph_e = ph_s + len(ph_r)

            responsec = {
                "text": text_e,
                "items": [
                    {
                        "start": ph_s,
                        "end": ph_e,
                        "entity_type": "PHONE NUMBER",
                        "text": ph_r,
                        "operator": "genz"
                        },
                    {
                        "start": p_s,
                        "end": p_e,
                        "entity_type": "PERSON",
                        "text": p_r,
                        "operator": "genz"
                    }
                ]
            }
            responsec["items"].sort(key=lambda x: x["start"])
            responsed = json.dumps(responsec)
            return Response(responsed, mimetype='application/json')
        @self.app.route("/deanonymize", methods=["POST"])
        def deanonymize() -> Response:
            content = request.get_json()
            if not content:
                raise BadRequest("Invalid request json")
            text = content.get("text", "")
            deanonymize_entities = AppEntitiesConvertor.deanonymize_entities_from_json(
                content
            )
            deanonymize_config = AppEntitiesConvertor.operators_config_from_json(
                content.get("deanonymizers")
            )
            deanonymized_response = self.deanonymize.deanonymize(
                text=text, entities=deanonymize_entities, operators=deanonymize_config
            )
            return Response(
                deanonymized_response.to_json(), mimetype="application/json"
            )

        @self.app.route("/anonymizers", methods=["GET"])
        def anonymizers():
            """Return a list of supported anonymizers."""
            return jsonify(self.anonymizer.get_anonymizers())

        @self.app.route("/deanonymizers", methods=["GET"])
        def deanonymizers():
            """Return a list of supported deanonymizers."""
            return jsonify(self.deanonymize.get_deanonymizers())

        @self.app.errorhandler(InvalidParamError)
        def invalid_param(err):
            self.logger.warning(
                f"Request failed with parameter validation error: {err.err_msg}"
            )
            return jsonify(error=err.err_msg), 422

        @self.app.errorhandler(HTTPException)
        def http_exception(e):
            return jsonify(error=e.description), e.code

        @self.app.errorhandler(Exception)
        def server_error(e):
            self.logger.error(f"A fatal error occurred during execution: {e}")
            return jsonify(error="Internal server error"), 500

def create_app(): # noqa
    server = Server()
    return server.app

if __name__ == "__main__":
    app = create_app()
    port = int(os.environ.get("PORT", DEFAULT_PORT))
    app.run(host="0.0.0.0", port=port)
