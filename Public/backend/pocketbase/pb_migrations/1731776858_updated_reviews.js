/// <reference path="../pb_data/types.d.ts" />
migrate((db) => {
  const dao = new Dao(db)
  const collection = dao.findCollectionByNameOrId("xhyyijrvsve6z0q")

  // add
  collection.schema.addField(new SchemaField({
    "system": false,
    "id": "cvjtwtrb",
    "name": "labels",
    "type": "relation",
    "required": false,
    "presentable": false,
    "unique": false,
    "options": {
      "collectionId": "x0gcs594596jebj",
      "cascadeDelete": false,
      "minSelect": null,
      "maxSelect": null,
      "displayFields": null
    }
  }))

  return dao.saveCollection(collection)
}, (db) => {
  const dao = new Dao(db)
  const collection = dao.findCollectionByNameOrId("xhyyijrvsve6z0q")

  // remove
  collection.schema.removeField("cvjtwtrb")

  return dao.saveCollection(collection)
})
