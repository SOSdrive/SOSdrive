// Create the profile for the authenticated user.
query "user_profile" verb=POST {
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

    precondition ($existing_profile == null) {
      error_type = "standard"
      error = "Profile already exists."
    }

    db.add user_profile {
      data = {
        user_id: $auth.id
        nome_completo: $input.nome_completo
        cpf: $input.cpf
        telefone: $input.telefone
        foto_perfil: $input.foto_perfil
      }
    } as $profile
  }

  response = $profile
  tags = ["sosdrive:profile"]
  guid = "0bonvKunIyoRgrgkhd3WrIa4zo0"
}
