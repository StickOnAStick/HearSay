/// <reference path="../pb_data/types.d.ts" />
migrate((db) => {
  const dao = new Dao(db)
  const collection = dao.findCollectionByNameOrId("xhyyijrvsve6z0q")

  collection.listRule = "@request.auth.id != ''"
  collection.updateRule = "@request.auth.id != ''"

  return dao.saveCollection(collection)
}, (db) => {
  const dao = new Dao(db)
  const collection = dao.findCollectionByNameOrId("xhyyijrvsve6z0q")

  collection.listRule = "@request.auth.id != '' && labels:length = 0"
  collection.updateRule = null

  return dao.saveCollection(collection)
})
