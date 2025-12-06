# Troubleshooting Guide

## Erro 401 Unauthorized no Upload do YouTube

### Sintoma
```
Failed to initialize upload: 401 Client Error: Unauthorized
```

### Causas Possíveis

1. **YouTube Data API v3 não habilitada no projeto**
   - Acesse: https://console.cloud.google.com/apis/library/youtube.googleapis.com
   - Verifique se a API está habilitada para seu projeto
   - Se não estiver, clique em "Enable"

2. **Redirect URI não configurado no OAuth**
   - Acesse: https://console.cloud.google.com/apis/credentials
   - Edite suas credenciais OAuth 2.0
   - Adicione `http://localhost:8088/callback` aos URIs de redirecionamento autorizados
   - Salve as alterações

3. **Escopos OAuth insuficientes**
   - O aplicativo precisa dos seguintes escopos:
     - `https://www.googleapis.com/auth/youtube.upload`
     - `https://www.googleapis.com/auth/youtube`
   - Verifique se ambos estão configurados no Google Cloud Console

4. **Projeto em modo de teste**
   - Se o projeto está em modo de teste, apenas usuários de teste podem fazer upload
   - Acesse: https://console.cloud.google.com/apis/credentials/consent
   - Adicione seu email como usuário de teste
   - OU publique o aplicativo (requer revisão do Google)

5. **Token inválido ou expirado**
   - Remova os tokens antigos: `rm ~/.ab_publisher_tokens.json`
   - Faça uma nova autenticação: `python3 ab/dc/publishers/cli_publisher.py auth`

### Solução Passo a Passo

1. **Verificar configuração do projeto Google Cloud:**
   ```bash
   # 1. Acesse https://console.cloud.google.com/
   # 2. Selecione seu projeto
   # 3. Navegue para "APIs & Services" > "Library"
   # 4. Procure por "YouTube Data API v3"
   # 5. Clique em "Enable" se não estiver habilitada
   ```

2. **Configurar OAuth 2.0:**
   ```bash
   # 1. Acesse https://console.cloud.google.com/apis/credentials
   # 2. Clique em suas credenciais OAuth 2.0
   # 3. Em "Authorized redirect URIs", adicione:
   #    http://localhost:8088/callback
   # 4. Salve
   ```

3. **Adicionar usuário de teste (se em modo de teste):**
   ```bash
   # 1. Acesse https://console.cloud.google.com/apis/credentials/consent
   # 2. Em "Test users", clique em "Add Users"
   # 3. Adicione seu email do Google
   # 4. Salve
   ```

4. **Reautenticar:**
   ```bash
   # Remover tokens antigos
   rm ~/.ab_publisher_tokens.json
   
   # Nova autenticação
   python3 ab/dc/publishers/cli_publisher.py auth
   ```

5. **Testar upload:**
   ```bash
   python3 ab/dc/publishers/cli_publisher.py upload \
     downloads/9x16/RusBe_8arLQ_9x16.mp4 \
     --title "Test video" \
     --description "Test" \
     --privacy private
   ```

### Debug Adicional

Se o problema persistir, execute com log detalhado:

```bash
# Exibir token sendo usado (primeiros 50 caracteres)
python3 ab/dc/publishers/cli_publisher.py upload \
  video.mp4 \
  --title "Test" \
  --privacy private 2>&1 | grep "Using access token"
```

```bash
# Verificar se token está válido
python3 -c "
from datetime import datetime
import json

with open('$HOME/.ab_publisher_tokens.json') as f:
    tokens = json.load(f)
    expiry = datetime.fromisoformat(tokens['youtube']['token_expiry'])
    print(f'Token expira em: {expiry}')
    print(f'Expirou: {expiry < datetime.now()}')
    print(f'Access token (50 chars): {tokens[\"youtube\"][\"access_token\"][:50]}...')
"
```

### Outros Erros Comuns

#### Erro 403 Forbidden
- **Causa:** Quota da API excedida ou permissões insuficientes
- **Solução:** 
  - Verifique quota em https://console.cloud.google.com/apis/api/youtube.googleapis.com/quotas
  - Aguarde reset diário (00:00 PST)
  - Ou solicite aumento de quota

#### Erro 400 Bad Request
- **Causa:** Metadata inválido (título, descrição, tags, etc.)
- **Solução:**
  - Verifique se título tem no máximo 100 caracteres
  - Descrição máximo 5000 caracteres
  - Tags máximo 500 caracteres no total
  - Categoria válida

#### Timeout durante upload
- **Causa:** Arquivo muito grande ou conexão lenta
- **Solução:**
  - Use vídeo menor para teste
  - Verifique conexão de internet
  - Upload pode levar vários minutos para vídeos grandes

## Porta em uso (Address already in use)

### Sintoma
```
[Errno 48] Address already in use
```

### Solução
```bash
# Opção 1: Use porta diferente
# Edite ab/dc/publishers/.env:
YOUTUBE_REDIRECT_URI=http://localhost:8081/callback

# Opção 2: Libere a porta ocupada
lsof -i :8080 | grep LISTEN
# Anote o PID e execute:
kill <PID>
```

## Referências

- [YouTube Data API Documentation](https://developers.google.com/youtube/v3)
- [OAuth 2.0 Setup](https://developers.google.com/youtube/registering_an_application)
- [API Quotas](https://developers.google.com/youtube/v3/getting-started#quota)
