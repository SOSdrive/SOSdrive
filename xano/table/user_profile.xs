// Stores the profile fields separate from authentication credentials.
table user_profile {
  auth = false

  schema {
    int id
    timestamp created_at?=now
    int user_id {
      table = "user"
      description = "Authenticated owner of this profile"
    }
    text nome_completo? filters=trim
    text cpf? filters=trim
    text telefone? filters=trim
    text foto_perfil? filters=trim
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree|unique", field: [{name: "user_id"}]}
  ]

  tags = ["sosdrive:profile"]
  guid = "UpFWjTDgBfFxMIU_j2wja7cRKrE"
}
