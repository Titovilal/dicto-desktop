use serde::{Deserialize, Serialize};
use std::time::Duration;

#[derive(Debug, Serialize, Deserialize)]
pub struct EditResult {
    pub text: String,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub enum EditError {
    APIKeyError,
    NetworkError(String),
    UnknownError(String),
}

impl std::fmt::Display for EditError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            EditError::APIKeyError => write!(f, "Invalid or missing API key"),
            EditError::NetworkError(msg) => write!(f, "Network error: {}", msg),
            EditError::UnknownError(msg) => write!(f, "Unknown error: {}", msg),
        }
    }
}

#[derive(Debug, Deserialize)]
struct ApiEditResponse {
    text: Option<String>,
    error: Option<String>,
    #[serde(rename = "type")]
    error_type: Option<String>,
}

pub async fn edit_text(
    original_text: &str,
    instruction: &str,
    api_key: &str,
    model: &str,
    api_url: &str,
) -> Result<EditResult, EditError> {
    let url = format!("{}/api/edit", api_url.trim_end_matches('/'));

    let client = reqwest::Client::builder()
        .timeout(Duration::from_secs(60))
        .build()
        .map_err(|e| EditError::NetworkError(e.to_string()))?;

    let body = serde_json::json!({
        "text": original_text,
        "instruction": instruction,
        "model": model,
    });

    let response = client
        .post(&url)
        .header("Authorization", format!("Bearer {}", api_key))
        .header("Content-Type", "application/json")
        .json(&body)
        .send()
        .await
        .map_err(|e| EditError::NetworkError(e.to_string()))?;

    let status = response.status();

    match status.as_u16() {
        401 | 403 => return Err(EditError::APIKeyError),
        200..=299 => {
            let api_resp: ApiEditResponse = response.json().await.map_err(|e| {
                EditError::UnknownError(format!("Failed to parse response: {}", e))
            })?;

            if let Some(text) = api_resp.text {
                return Ok(EditResult { text });
            }

            let err_msg = api_resp.error.unwrap_or_else(|| "Empty response".to_string());
            Err(map_edit_error(&err_msg, api_resp.error_type.as_deref()))
        }
        _ => {
            let err_text = response
                .text()
                .await
                .unwrap_or_else(|_| format!("HTTP {}", status));

            if let Ok(body) = serde_json::from_str::<ApiEditResponse>(&err_text) {
                let msg = body.error.unwrap_or(err_text.clone());
                Err(map_edit_error(&msg, body.error_type.as_deref()))
            } else {
                Err(EditError::UnknownError(err_text))
            }
        }
    }
}

fn map_edit_error(message: &str, error_type: Option<&str>) -> EditError {
    let lower = message.to_lowercase();
    if let Some(t) = error_type {
        match t {
            "api_key_error" | "authentication_error" => return EditError::APIKeyError,
            _ => {}
        }
    }
    if lower.contains("api key") || lower.contains("unauthorized") || lower.contains("authentication") {
        EditError::APIKeyError
    } else if lower.contains("network") || lower.contains("connection") {
        EditError::NetworkError(message.to_string())
    } else {
        EditError::UnknownError(message.to_string())
    }
}
