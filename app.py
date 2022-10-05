import os

from flask import Flask
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_smorest import Api

import models
from blocklist import BLOCKLIST
from db import db
from resources.item import blp as ItemBluePrint
from resources.store import blp as StoreBluePrint
from resources.tag import blp as TagBluePrint
from resources.user import blp as UserBluePrint


def create_app():
    app = Flask(__name__)

    app.config["API_TITLE"] = "Stores REST API"
    app.config["API_VERSION"] = "v1"
    app.config["PROPAGETE_EXCEPTIONS"] = True
    app.config["OPENAPI_VERSION"] = "3.0.2"
    app.config["OPENAPI_URL_PREFIX"] = "/"
    app.config["OPENAPI_SWAGGER_UI_PATH"] = "/swagger"
    app.config[
        "OPENAPI_SWAGGER_UI_URL"
    ] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "DATABASE_URL", "sqlite:///data.db"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    migrate = Migrate(app, db)
    api = Api(app)
    app.config["JWT_SECRET_KEY"] = "super-secret"  # Change this!
    jwt = JWTManager(app)

    @jwt.token_in_blocklist_loader
    def check_if_token_in_blocklist(jwt_header, jwt_payload):
        jti = jwt_payload["jti"]
        return jti in BLOCKLIST

    @jwt.revoked_token_loader
    def revoked_token_callback():
        return (
            {"description": "The token has been revoked", "error": "token_revoked"},
            401,
        )

    @jwt.additional_claims_loader
    def add_claims_to_access_token(identity):
        user = models.UserModel.query.get(identity)
        if user.username == "admin":
            return {"is_admin": True}
        return {"is_admin": False}

    @jwt.expired_token_loader
    def my_expired_token_callback():
        return {"description": "The token has expired.", "error": "token_expired"}, 401

    @jwt.invalid_token_loader
    def my_invalid_token_callback(error):
        return {
            "description": "Signature verification failed.",
            "error": "invalid_token",
        }, 401

    @jwt.unauthorized_loader
    def my_unauthorized_callback(error):
        return {
            "description": "Request does not contain an access token.",
            "error": "authorization_required",
        }, 401

    with app.app_context():
        db.create_all()
    api.register_blueprint(ItemBluePrint)
    api.register_blueprint(StoreBluePrint)
    api.register_blueprint(TagBluePrint)
    api.register_blueprint(UserBluePrint)
    return app
