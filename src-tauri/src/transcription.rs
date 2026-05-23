use serde::{Deserialize, Serialize};
use std::time::Duration;

#[derive(Debug, Serialize, Deserialize)]
pub struct TranscriptionResult {
    pub text: String,
    pub transcription_id: Option<String>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub enum TranscriptionError {
    APIKeyError,
    RateLimitError,
    AudioTooShortError,
    AudioTooLongError,
    NetworkError(String),
    UnknownError(String),
}

impl std::fmt::Display for TranscriptionError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            TranscriptionError::APIKeyError => write!(f, "Invalid or missing API key"),
            TranscriptionError::RateLimitError => write!(f, "Rate limit exceeded"),
            TranscriptionError::AudioTooShortError => write!(f, "Audio is too short"),
            TranscriptionError::AudioTooLongError => write!(f, "Audio is too long"),
            TranscriptionError::NetworkError(msg) => write!(f, "Network error: {}", msg),
            TranscriptionError::UnknownError(msg) => write!(f, "Unknown error: {}", msg),
        }
    }
}

#[derive(Debug, Deserialize)]
struct ApiResponse {
    text: Option<String>,
    transcription_id: Option<String>,
    error: Option<String>,
    #[serde(rename = "type")]
    error_type: Option<String>,
}

pub async fn transcribe(
    audio_bytes: Vec<u8>,
    api_key: &str,
    model: &str,
    language: &str,
    api_url: &str,
) -> Result<TranscriptionResult, TranscriptionError> {
    let url = format!("{}/api/transcribe", api_url.trim_end_matches('/'));

    let client = reqwest::Client::builder()
        .timeout(Duration::from_secs(60))
        .build()
        .map_err(|e| TranscriptionError::NetworkError(e.to_string()))?;

    let mut last_error = TranscriptionError::UnknownError("No attempts made".to_string());
    let backoff_ms = [1000u64, 2000, 4000];

    for attempt in 0..3usize {
        let file_part = reqwest::multipart::Part::bytes(audio_bytes.clone())
            .file_name("audio.wav")
            .mime_str("audio/wav")
            .map_err(|e| TranscriptionError::NetworkError(e.to_string()))?;

        let form = reqwest::multipart::Form::new()
            .part("file", file_part)
            .text("model", model.to_string())
            .text("language", language.to_string());

        let response = client
            .post(&url)
            .header("Authorization", format!("Bearer {}", api_key))
            .multipart(form)
            .send()
            .await;

        match response {
            Err(e) => {
                last_error = TranscriptionError::NetworkError(e.to_string());
                if attempt < 2 {
                    tokio::time::sleep(Duration::from_millis(backoff_ms[attempt])).await;
                }
                continue;
            }
            Ok(resp) => {
                let status = resp.status();

                match status.as_u16() {
                    401 | 403 => return Err(TranscriptionError::APIKeyError),
                    429 => {
                        last_error = TranscriptionError::RateLimitError;
                        if attempt < 2 {
                            tokio::time::sleep(Duration::from_millis(backoff_ms[attempt])).await;
                        }
                        continue;
                    }
                    200..=299 => {
                        let body: ApiResponse = resp.json().await.map_err(|e| {
                            TranscriptionError::UnknownError(format!("Failed to parse response: {}", e))
                        })?;

                        if let Some(text) = body.text {
                            return Ok(TranscriptionResult {
                                text,
                                transcription_id: body.transcription_id,
                            });
                        }

                        let err_msg = body.error.unwrap_or_else(|| "Empty response".to_string());
                        return Err(map_api_error(&err_msg, body.error_type.as_deref()));
                    }
                    _ => {
                        let err_text = resp
                            .text()
                            .await
                            .unwrap_or_else(|_| format!("HTTP {}", status));

                        // Try to parse JSON error
                        if let Ok(body) = serde_json::from_str::<ApiResponse>(&err_text) {
                            let msg = body.error.unwrap_or(err_text.clone());
                            last_error = map_api_error(&msg, body.error_type.as_deref());
                        } else {
                            last_error = TranscriptionError::UnknownError(err_text);
                        }

                        if attempt < 2 {
                            tokio::time::sleep(Duration::from_millis(backoff_ms[attempt])).await;
                        }
                        continue;
                    }
                }
            }
        }
    }

    Err(last_error)
}

fn map_api_error(message: &str, error_type: Option<&str>) -> TranscriptionError {
    let lower = message.to_lowercase();
    if let Some(t) = error_type {
        match t {
            "api_key_error" | "authentication_error" => return TranscriptionError::APIKeyError,
            "rate_limit_error" => return TranscriptionError::RateLimitError,
            "audio_too_short" => return TranscriptionError::AudioTooShortError,
            "audio_too_long" => return TranscriptionError::AudioTooLongError,
            _ => {}
        }
    }
    if lower.contains("api key") || lower.contains("unauthorized") || lower.contains("authentication") {
        TranscriptionError::APIKeyError
    } else if lower.contains("rate limit") {
        TranscriptionError::RateLimitError
    } else if lower.contains("too short") {
        TranscriptionError::AudioTooShortError
    } else if lower.contains("too long") {
        TranscriptionError::AudioTooLongError
    } else {
        TranscriptionError::UnknownError(message.to_string())
    }
}
