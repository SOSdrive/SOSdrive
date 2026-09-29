// Table to store user vehicles
table vehicle {
  schema {
    int id
    timestamp created_at?=now
    int user_id {
      table = "user"
      description = "Authenticated owner of this vehicle"
    }
    text brand
    text model
    text plate
    int year
    text color
  }

  index = [
    {type: "primary", field: [{name: "id"}]},
    {type: "btree", field: [{name: "user_id", op: "asc"}]}
  ]
  guid = "JixBl5ZTqT_XzgUdBDQQ1qKJ3fU"
}