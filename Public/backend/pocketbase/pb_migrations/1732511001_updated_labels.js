/// <reference path="../pb_data/types.d.ts" />
migrate((db) => {
  const dao = new Dao(db)
  const collection = dao.findCollectionByNameOrId("x0gcs594596jebj")

  // update
  collection.schema.addField(new SchemaField({
    "system": false,
    "id": "8ojvgh6b",
    "name": "overall_sentiment",
    "type": "number",
    "required": false,
    "presentable": false,
    "unique": false,
    "options": {
      "min": -1,
      "max": 1,
      "noDecimal": false
    }
  }))

  return dao.saveCollection(collection)
}, (db) => {
  const dao = new Dao(db)
  const collection = dao.findCollectionByNameOrId("x0gcs594596jebj")

  // update
  collection.schema.addField(new SchemaField({
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
  }))

  return dao.saveCollection(collection)
})
