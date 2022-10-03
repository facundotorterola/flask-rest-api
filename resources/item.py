from flask.views import MethodView
from flask_smorest import Blueprint, abort
from models.item import ItemModel
from schemas import ItemSchema, ItemUpdateSchema
from db import db
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from flask_jwt_extended import jwt_required, get_jwt

blp = Blueprint("items", __name__, description="Items")


@blp.route("/item")
class ItemList(MethodView):
    @blp.response(200, ItemSchema(many=True))
    def get(self):
        return ItemModel.query.all()

    @jwt_required()
    @blp.response(201, ItemSchema)
    @blp.arguments(ItemSchema)
    def post(self, item_data):
        item = ItemModel(**item_data)

        try:
            db.session.add(item)
            db.session.commit()
        except IntegrityError as e:
            print(e)
            abort(400, message="The item with that name already exists.")
        except SQLAlchemyError as e:
            print(e)
            abort(500, message="An error occurred inserting the item.")

        return item


@blp.route("/item/<int:item_id>")
class Item(MethodView):
    @blp.response(200, ItemSchema)
    def get(self, item_id):
        item = ItemModel.query.get_or_404(item_id)
        return item

    @jwt_required()
    def delete(self, item_id):
        jwt = get_jwt()

        if not jwt["is_admin"]:
            abort(403, message="You are not authorized to delete items.")

        item = ItemModel.query.get_or_404(item_id)
        db.session.delete(item)
        db.session.commit()
        return {"message": "Item deleted"}, 200

    @blp.arguments(ItemUpdateSchema)
    @blp.response(200, ItemSchema)
    def put(self, update_item, item_id):
        item = ItemModel.query.get(item_id)
        if item:
            item.name = update_item["name"]
            item.price = update_item["price"]
        else:
            item = ItemModel(id=item_id, **update_item)

        db.session.add(item)
        db.session.commit()

        return item
