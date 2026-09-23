// Get the profile belonging to the authenticated user.
query "user_profile" verb=GET {
  api_group = "Authentication"
  auth = "user"

  input {
  }

  stack {
    db.get user_profile {
      field_name = "user_id"
      field_value = $auth.id
      output = ["id", "user_id", "nome_completo", "cpf", "telefone", "foto_perfil"]
    } as $profile
  }

  response = $profile
  tags = ["sosdrive:profile"]
  guid = "_Fo_-u7nQAIWx4QB-WqfbnNnhMQ"
}
