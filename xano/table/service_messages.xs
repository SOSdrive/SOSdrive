// Messages exchanged during a service request
table service_messages {
  schema {
    int id
    int service_request_id {
      table = "service_request"
      description = "Service request that owns this message"
    }
    int sender_id {
      table = "user"
      description = "Authenticated user that sent this message"
    }
    text message_text filters=trim
    timestamp created_at?=now
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "service_request_id"}, {name: "created_at", op: "asc"}]}
    {type: "btree", field: [{name: "sender_id", op: "asc"}]}
  ]
}