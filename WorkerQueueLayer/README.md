# Worker Queue Layer

Reference the DrawIo schematic found in `DesignDocuments/v0.0.0.drawio`.

This directory hosts the RabbitMQ message (work) broker as well as the code for each worker. 

The workers have a top level utils package they import to perform aggregation. 

All workers have connections to DB and cache. 