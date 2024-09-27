docker run -d \
  --hostname my-rabbit \
  --name rabbitmq \
  -p 5672:5672 \
  -p 15672:15672 \
  -v $(pwd)/rabbitmq/log:/var/log/rabbitmq \
  -v $(pwd)/rabbitmq/conf/rabbitmq.conf:/etc/rabbitmq/rabbitmq.conf \
  -e RABBITMQ_DEFAULT_USER=guest \
  -e RABBITMQ_DEFAULT_PASS=guest \
  rabbitmq:3-management

# IDK if this will be needed for now.