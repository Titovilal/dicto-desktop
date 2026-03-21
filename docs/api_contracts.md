# Contratos de API - Dicto Desktop

**Base URL:** `https://terturionsland.dev` (configurable via `DICTO_API_URL`)

---

## POST /api/transcribe

### Request

**Headers:**
- `Authorization: Bearer {api_key}`

**Body (multipart/form-data):**

| Campo      | Tipo   | Requerido | Descripción                                      |
|------------|--------|-----------|--------------------------------------------------|
| `file`     | binary | Sí        | Archivo de audio (.wav, .mp3, .webm, .m4a, .ogg) |
| `source`   | string | Sí        | Siempre `"mic_app"`                              |
| `model`    | string | Sí        | Modelo a usar (default: `"v3-turbo"`)            |
| `language` | string | No        | Código de idioma (default: `"es"`)               |

**Validaciones:**
- Tamaño del archivo: 0.001 MB ≤ size ≤ 25 MB

### Response (200)

```json
{
  "text": "string",
  "id": 123,
  "language": "es",
  "duration": 3.45
}
```

### Errores

| Código | Excepción         | Descripción                  |
|--------|-------------------|------------------------------|
| 401    | `APIKeyError`     | API key inválida o faltante  |
| 429    | `RateLimitError`  | Límite de uso alcanzado      |
| Otro   | `TranscriptionError` | Error genérico con mensaje |

**Reintentos:** Máximo 3 con backoff exponencial (2s, 4s, 8s).

---

## POST /api/transform

### Request

**Headers:**
- `Authorization: Bearer {api_key}`
- `Content-Type: application/json`

**Body (JSON):**

```json
{
  "text": "string",
  "instructions": "string",
  "transcriptionId": 123
}
```

| Campo             | Tipo        | Requerido | Descripción                                    |
|-------------------|-------------|-----------|------------------------------------------------|
| `text`            | string      | Sí        | Texto a transformar                            |
| `instructions`    | string      | Sí        | Prompt/instrucciones de transformación         |
| `transcriptionId` | int \| null | No        | ID de la transcripción original (si aplica)    |

### Response (200)

```json
{
  "choices": [
    {
      "message": {
        "content": "string"
      }
    }
  ]
}
```

El texto transformado se extrae de `choices[0].message.content`.

### Errores

| Código | Excepción         | Descripción                  |
|--------|-------------------|------------------------------|
| 401    | `APIKeyError`     | API key inválida o faltante  |
| 429    | `RateLimitError`  | Límite de uso alcanzado      |
| Otro   | `TranscriptionError` | Error genérico con mensaje |

### Formatos predefinidos en la app

| format_id | instructions                                                                                          |
|-----------|-------------------------------------------------------------------------------------------------------|
| `email`   | Reescribe el siguiente texto como un correo electrónico profesional. Mantén el idioma original del texto. |
| `notes`   | Convierte el siguiente texto en notas organizadas con viñetas. Mantén el idioma original del texto.   |
| `tweet`   | Reescribe el siguiente texto como un post corto para redes sociales. Mantén el idioma original del texto. |

---

## Estructura de errores del servidor

```json
{
  "error": {
    "message": "string"
  }
}
```

o

```json
{
  "error": "string"
}
```
