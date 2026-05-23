use serde::{Deserialize, Serialize};
use std::time::Duration;

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct Preset {
    pub id: String,
    pub name: String,
    pub description: Option<String>,
    pub prompt: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct TransformResult {
    pub text: String,
}

#[derive(Debug, Deserialize)]
struct PresetsResponse {
    presets: Option<Vec<Preset>>,
}

#[derive(Debug, Deserialize)]
struct ApiTransformResponse {
    text: Option<String>,
    error: Option<String>,
    #[serde(rename = "type")]
    error_type: Option<String>,
}

/// Fetches the user's favorite presets from GET /api/presets
/// Headers: Authorization: Bearer {api_key}
pub async fn fetch_presets(api_key: &str, api_url: &str) -> Result<Vec<Preset>, String> {
    let url = format!("{}/api/presets", api_url.trim_end_matches('/'));

    let client = reqwest::Client::builder()
        .timeout(Duration::from_secs(30))
        .build()
        .map_err(|e| format!("NetworkError: {}", e))?;

    let response = client
        .get(&url)
        .header("Authorization", format!("Bearer {}", api_key))
        .send()
        .await
        .map_err(|e| format!("NetworkError: {}", e))?;

    let status = response.status();

    match status.as_u16() {
        401 | 403 => Err("APIKeyError".to_string()),
        200..=299 => {
            let body = response
                .text()
                .await
                .map_err(|e| format!("NetworkError: {}", e))?;

            // Try to parse as array directly first, then as object with presets field
            if let Ok(presets) = serde_json::from_str::<Vec<Preset>>(&body) {
                return Ok(presets);
            }
            if let Ok(resp) = serde_json::from_str::<PresetsResponse>(&body) {
                return Ok(resp.presets.unwrap_or_default());
            }
            Err(format!("NetworkError: Failed to parse presets response"))
        }
        _ => {
            let err_text = response
                .text()
                .await
                .unwrap_or_else(|_| format!("HTTP {}", status));
            Err(format!("NetworkError: {}", err_text))
        }
    }
}

/// Transforms text using POST /api/transform
/// Body JSON: { text, prompt, model, transcription_id? }
/// Headers: Authorization: Bearer {api_key}
pub async fn transform_text(
    text: &str,
    prompt: &str,
    model: &str,
    api_key: &str,
    transcription_id: Option<&str>,
    api_url: &str,
) -> Result<TransformResult, String> {
    let url = format!("{}/api/transform", api_url.trim_end_matches('/'));

    let client = reqwest::Client::builder()
        .timeout(Duration::from_secs(60))
        .build()
        .map_err(|e| format!("NetworkError: {}", e))?;

    let mut body = serde_json::json!({
        "text": text,
        "prompt": prompt,
        "model": model,
    });

    if let Some(tid) = transcription_id {
        body["transcription_id"] = serde_json::Value::String(tid.to_string());
    }

    let response = client
        .post(&url)
        .header("Authorization", format!("Bearer {}", api_key))
        .header("Content-Type", "application/json")
        .json(&body)
        .send()
        .await
        .map_err(|e| format!("NetworkError: {}", e))?;

    let status = response.status();

    match status.as_u16() {
        401 | 403 => Err("APIKeyError".to_string()),
        200..=299 => {
            let api_resp: ApiTransformResponse = response
                .json()
                .await
                .map_err(|e| format!("NetworkError: Failed to parse response: {}", e))?;

            if let Some(transformed) = api_resp.text {
                return Ok(TransformResult { text: transformed });
            }

            let err_msg = api_resp.error.unwrap_or_else(|| "Empty response".to_string());
            Err(err_msg)
        }
        _ => {
            let err_text = response
                .text()
                .await
                .unwrap_or_else(|_| format!("HTTP {}", status));

            if let Ok(body) = serde_json::from_str::<ApiTransformResponse>(&err_text) {
                Err(body.error.unwrap_or(err_text.clone()))
            } else {
                Err(format!("NetworkError: {}", err_text))
            }
        }
    }
}
