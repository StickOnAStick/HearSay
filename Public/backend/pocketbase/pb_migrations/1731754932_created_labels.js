/// <reference path="../pb_data/types.d.ts" />
migrate((db) => {
  const collection = new Collection({
    "id": "x0gcs594596jebj",
    "created": "2024-11-16 11:02:12.161Z",
    "updated": "2024-11-16 11:02:12.161Z",
    "name": "labels",
    "type": "base",
    "system": false,
    "schema": [
      {
        "system": false,
        "id": "5fvpaaos",
        "name": "keywords",
        "type": "json",
        "required": false,
        "presentable": false,
        "unique": false,
        "options": {
          "maxSize": 2000000
        }
      },
      {
        "system": false,
        "id": "8ojvgh6b",
        "name": "sentiment",
        "type": "number",
        "required": false,
        "presentable": false,
        "unique": false,
        "options": {
          "min": -1,
          "max": 1,
          "noDecimal": false
        }
      },
      {
        "system": false,
        "id": "r2uycz65",
        "name": "review_id",
        "type": "relation",
        "required": false,
        "presentable": false,
        "unique": false,
        "options": {
          "collectionId": "xhyyijrvsve6z0q",
          "cascadeDelete": false,
          "minSelect": null,
          "maxSelect": 1,
          "displayFields": null
        }
      }
    ],
    "indexes": [],
    "listRule": "",
    "viewRule": "",
    "createRule": "",
    "updateRule": null,
    "deleteRule": null,
    "options": {}
  });

  return Dao(db).saveCollection(collection);
}, (db) => {
  const dao = new Dao(db);
  const collection = dao.findCollectionByNameOrId("x0gcs594596jebj");

  return dao.deleteCollection(collection);
})
