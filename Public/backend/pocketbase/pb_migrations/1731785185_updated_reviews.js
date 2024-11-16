/// <reference path="../pb_data/types.d.ts" />
migrate((db) => {
  const dao = new Dao(db)
  const collection = dao.findCollectionByNameOrId("xhyyijrvsve6z0q")

  collection.listRule = "@request.auth.id != '' && labels = null"

  return dao.saveCollection(collection)
}, (db) => {
  const dao = new Dao(db)
  const collection = dao.findCollectionByNameOrId("xhyyijrvsve6z0q")

  collection.listRule = "@request.auth.id != ''"

  return dao.saveCollection(collection)
})
