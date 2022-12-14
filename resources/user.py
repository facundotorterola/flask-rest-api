from flask.views import MethodView
from flask_jwt_extended import create_access_token, get_jwt, jwt_required
from flask_smorest import Blueprint, abort
from passlib.hash import pbkdf2_sha256 as sha256
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from blocklist import BLOCKLIST
from db import db
from models import UserModel
from schemas import UserSchema

blp = Blueprint("users", __name__, description="users")


@blp.route("/register")
class UserRegister(MethodView):
    @blp.arguments(UserSchema)
    @blp.response(201, UserSchema)
    def post(self, user_data):

        user_data["password"] = sha256.hash(user_data["password"])

        user = UserModel(**user_data)

        try:
            db.session.add(user)
            db.session.commit()

        except IntegrityError as e:
            print(e)
            abort(400, message="The user with that username already exists.")
        except SQLAlchemyError as e:
            print(e)
            abort(500, message="An error occurred inserting the user.")

        return user


@blp.route("/user/<int:user_id>")
class User(MethodView):
    @blp.response(200, UserSchema)
    def get(self, user_id):
        user = UserModel.query.get_or_404(user_id)
        return user

    def delete(self, user_id):
        user = UserModel.query.get_or_404(user_id)
        db.session.delete(user)
        db.session.commit()
        return {"message": "User deleted"}, 200


@blp.route("/login")
class UserLogin(MethodView):
    @blp.arguments(UserSchema)
    def post(self, user_data):
        user = UserModel.query.filter_by(username=user_data["username"]).first()
        if user and sha256.verify(user_data["password"], user.password):
            access_token = create_access_token(identity=user.id, fresh=True)
            refresh_token = create_access_token(identity=user.id, fresh=False)
            return {"access_token": access_token, "refresh_token": refresh_token}, 200
        return {"message": "Invalid credentials"}, 401


@blp.route("/logout")
class UserLogout(MethodView):
    @jwt_required()
    def post(self):
        jti = get_jwt()["jti"]
        BLOCKLIST.add(jti)
        return {"message": "User logged out"}, 200


@blp.route("/refresh")
class UserRefresh(MethodView):
    @jwt_required(refresh=True)
    def post(self):
        current_user = get_jwt()["identity"]
        new_token = create_access_token(identity=current_user, fresh=False)
        return {"access_token": new_token}, 200
