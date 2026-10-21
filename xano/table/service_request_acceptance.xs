// Unique claim ensures only one provider can accept each service request.
table service_request_acceptance {
  schema {
    int id
    int service_request_id {
      table = "service_request"
      description = "Service request claimed by a provider"
    }
    int provider_id {
      table = "user"
      description = "Provider that claimed the service request"
    }
    timestamp created_at?=now
  }

  index = [
    {type: "primary", field: [{name: "id"}]},
    {type: "btree|unique", field: [{name: "service_request_id"}]}
  ]
}
