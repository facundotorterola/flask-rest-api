from flask import request
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from db_local import stores
from models.store import StoreModel
from models.tag import TagModel
from models.item import ItemModel
from schemas import PlainTagSchema, TagSchema
from db import db
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from flask_jwt_extended import jwt_required

blp = Blueprint("tags", __name__, description="Tags")


@blp.route("/store/<int:store_id>/tag")
class TagInStore(MethodView):
    @blp.response(200, TagSchema(many=True))
    def get(self, store_id):
        store = StoreModel.query.get_or_404(store_id)
        return store.tags.all()

    @jwt_required()
    @blp.arguments(PlainTagSchema)
    @blp.response(201, TagSchema)
    def post(self, tag_data, store_id):
        store = StoreModel.query.get_or_404(store_id)
        if store.tags.filter_by(name=tag_data["name"]).first():
            abort(400, message="The tag with that name already exists.")
        tag = TagModel(**tag_data, store_id=store_id)
        store.tags.append(tag)

        try:
            db.session.add(tag)
            db.session.commit()
        except IntegrityError as e:
            print(e)
            abort(400, message="The tag with that name already exists.")
        except SQLAlchemyError as e:
            print(e)
            abort(500, message="An error occurred inserting the tag.")

        return tag, 201


@blp.route("/item/<int:item_id>/tag/<int:tag_id>")
class TagInItems(MethodView):
    def delete(self, item_id, tag_id):
        tag = TagModel.query.get_or_404(tag_id)
        ItemModel.query.get_or_404(item_id)
        if tag.items.filter_by(id=item_id).first():
            tag.items.remove(item_id)
            db.session.commit()
            return {"message": "Tag removed from item"}, 200
        else:
            abort(400, message="The tag is not associated with that item.")

    @blp.response(201, TagSchema)
    def post(self, item_id, tag_id):
        tag = TagModel.query.get_or_404(tag_id)
        ItemModel.query.get_or_404(item_id)
        if tag.items.filter_by(id=item_id).first():
            abort(400, message="The tag is already associated with that item.")
        tag.items.append(item_id)

        try:
            db.session.add(tag)
            db.session.commit()
        except SQLAlchemyError as e:
            print(e)
            abort(500, message="An error occurred inserting the tag.")

        return tag, 201


@blp.route("/tag/<int:tag_id>")
class Tag(MethodView):
    @blp.response(200, TagSchema)
    def get(self, tag_id):
        tag = TagModel.query.get_or_404(tag_id)
        return tag

    @jwt_required()
    def delete(self, tag_id):
        tag = TagModel.query.get_or_404(tag_id)
        if tag.items.all():
            abort(400, message="The tag is associated with an item.")

        db.session.delete(tag)
        db.session.commit()
        return {"message": "Tag deleted"}, 200
