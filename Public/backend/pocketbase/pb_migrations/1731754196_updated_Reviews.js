/// <reference path="../pb_data/types.d.ts" />
migrate((db) => {
  const dao = new Dao(db)
  const collection = dao.findCollectionByNameOrId("1pj5vftl51f4qjh")

  // update
  collection.schema.addField(new SchemaField({
    "system": false,
    "id": "g96odsrp",
    "name": "id_",
    "type": "number",
    "required": false,
    "presentable": false,
    "unique": false,
    "options": {
      "min": null,
      "max": null,
      "noDecimal": false
    }
  }))

  return dao.saveCollection(collection)
}, (db) => {
  const dao = new Dao(db)
  const collection = dao.findCollectionByNameOrId("1pj5vftl51f4qjh")

  // update
  collection.schema.addField(new SchemaField({
    "system": false,
    "id": "g96odsrp",
    "name": "_id",
    "type": "number",
    "required": false,
    "presentable": false,
    "unique": false,
    "options": {
      "min": null,
      "max": null,
      "noDecimal": false
    }
  }))

  return dao.saveCollection(collection)
})
