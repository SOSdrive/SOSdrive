// Update the profile belonging to the authenticated user.
query "user_profile" verb=PUT {
  api_group = "Authentication"
  auth = "user"

  input {
    text nome_completo? filters=trim
    text cpf? filters=trim
    text telefone? filters=trim
    text foto_perfil? filters=trim
  }

  stack {
    precondition (($input.cpf == null) || (($input.cpf|strlen) == 0) || (($input.cpf|strlen) == 11)) {
      error_type = "inputerror"
      error = "CPF must contain 11 digits."
    }
    precondition (($input.telefone == null) || (($input.telefone|strlen) == 0) || (($input.telefone|strlen) == 10) || (($input.telefone|strlen) == 11)) {
      error_type = "inputerror"
      error = "Phone must contain 10 or 11 digits."
    }

    db.get user_profile {
      field_name = "user_id"
      field_value = $auth.id
    } as $existing_profile

    precondition ($existing_profile != null) {
      error_type = "notfound"
      error = "Profile not found."
    }

    db.edit user_profile {
      field_name = "user_id"
      field_value = $auth.id
      data = {
        nome_completo: $input.nome_completo
        cpf: $input.cpf
        telefone: $input.telefone
        foto_perfil: $input.foto_perfil
      }
    } as $profile
  }

  response = $profile
  tags = ["sosdrive:profile"]
  guid = "ic_-b6qd1nEMXp01hhh2Obxq9IA"
}
