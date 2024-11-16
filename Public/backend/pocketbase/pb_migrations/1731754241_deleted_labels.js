/// <reference path="../pb_data/types.d.ts" />
migrate((db) => {
  const dao = new Dao(db);
  const collection = dao.findCollectionByNameOrId("d91wvgnhqhea3a7");

  return dao.deleteCollection(collection);
}, (db) => {
  const collection = new Collection({
    "id": "d91wvgnhqhea3a7",
    "created": "2024-11-16 09:57:04.612Z",
    "updated": "2024-11-16 09:57:29.028Z",
    "name": "labels",
    "type": "base",
    "system": false,
    "schema": [
      {
        "system": false,
        "id": "op1vpdec",
        "name": "keywords",
        "type": "text",
        "required": false,
        "presentable": false,
        "unique": false,
        "options": {
          "min": null,
          "max": null,
          "pattern": ""
        }
      },
      {
        "system": false,
        "id": "yrkaunyb",
        "name": "review_id",
        "type": "relation",
        "required": false,
        "presentable": false,
        "unique": false,
        "options": {
          "collectionId": "1pj5vftl51f4qjh",
          "cascadeDelete": true,
          "minSelect": null,
          "maxSelect": 1,
          "displayFields": null
        }
      },
      {
        "system": false,
        "id": "jwndlnio",
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
      }
    ],
    "indexes": [],
    "listRule": null,
    "viewRule": null,
    "createRule": null,
    "updateRule": null,
    "deleteRule": null,
    "options": {}
  });

  return Dao(db).saveCollection(collection);
})
