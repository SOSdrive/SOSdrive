// Table to store service requests for assistance
table service_request {
  schema {
    int id
    timestamp created_at?=now
    timestamp updated_at?=now
    int user_id {
      table = "user"
      description = "Authenticated user requesting service"
    }
    int vehicle_id {
      table = "vehicle"
      description = "Vehicle used for the service"
    }
    text service_type
    decimal latitude
    decimal longitude
    decimal estimated_price
    decimal distance_km
    text status default="pending"
  }

  index = [
    {type: "primary", field: [{name: "id"}]},
    {type: "btree", field: [{name: "user_id", op: "asc"}]},
    {type: "btree", field: [{name: "created_at", op: "desc"}]}
  ]
  guid = "PJ8QmESUAbn4C3qIoIg5KGDn-n8"
}