use tauri::State;
use std::sync::Mutex;
use crate::audio::AudioRecorder;
use crate::transcription;

pub struct RecorderState(pub Mutex<AudioRecorder>);

#[tauri::command]
pub async fn start_recording(
    app: tauri::AppHandle,
    state: State<'_, RecorderState>,
) -> Result<(), String> {
    let recorder = state.0.lock().map_err(|e| e.to_string())?;
    recorder.start(app)
}

#[tauri::command]
pub async fn stop_recording(
    state: State<'_, RecorderState>,
) -> Result<Vec<u8>, String> {
    let native_rate = AudioRecorder::native_sample_rate();
    let samples = {
        let recorder = state.0.lock().map_err(|e| e.to_string())?;
        recorder.stop()
    };
    let wav_bytes = AudioRecorder::samples_to_wav(&samples, native_rate);
    Ok(wav_bytes)
}

#[derive(serde::Serialize)]
pub struct TranscribeResponse {
    pub text: String,
    pub transcription_id: Option<String>,
}

#[tauri::command]
pub async fn transcribe_audio(
    audio_bytes: Vec<u8>,
    api_key: String,
    model: String,
    language: String,
) -> Result<TranscribeResponse, String> {
    let api_url = std::env::var("DICTO_API_URL")
        .unwrap_or_else(|_| "https://dicto.up.railway.app".to_string());

    match transcription::transcribe(audio_bytes, &api_key, &model, &language, &api_url).await {
        Ok(result) => Ok(TranscribeResponse {
            text: result.text,
            transcription_id: result.transcription_id,
        }),
        Err(e) => Err(e.to_string()),
    }
}

#[tauri::command]
pub async fn list_audio_devices() -> Result<Vec<String>, String> {
    Ok(AudioRecorder::list_devices())
}

#[tauri::command]
pub async fn register_hotkeys(
    app: tauri::AppHandle,
    record_hotkey: String,
    edit_hotkey: String,
) -> Result<(), String> {
    crate::hotkeys::register_hotkeys(&app, &record_hotkey, &edit_hotkey)
}

#[tauri::command]
pub async fn update_app_status(
    app: tauri::AppHandle,
    status: String,
) -> Result<(), String> {
    use tauri::Emitter;
    crate::tray::update_tray_status(&app, &status);
    app.emit("app-status-changed", serde_json::json!({ "status": status }))
        .map_err(|e| e.to_string())?;
    Ok(())
}

#[tauri::command]
pub async fn show_main_window(app: tauri::AppHandle) -> Result<(), String> {
    use tauri::Manager;
    if let Some(win) = app.get_webview_window("main") {
        win.show().map_err(|e| e.to_string())?;
        win.set_focus().map_err(|e| e.to_string())?;
    }
    Ok(())
}

#[tauri::command]
pub async fn show_overlay(app: tauri::AppHandle) -> Result<(), String> {
    use tauri::Manager;
    if let Some(win) = app.get_webview_window("overlay") {
        win.show().map_err(|e| e.to_string())?;
    }
    Ok(())
}

#[tauri::command]
pub async fn hide_overlay(app: tauri::AppHandle) -> Result<(), String> {
    use tauri::Manager;
    if let Some(win) = app.get_webview_window("overlay") {
        win.hide().map_err(|e| e.to_string())?;
    }
    Ok(())
}

#[tauri::command]
pub async fn start_edit_flow(
    app: tauri::AppHandle,
    state: State<'_, RecorderState>,
) -> Result<(), String> {
    use tauri::Emitter;

    crate::keyboard::simulate_copy()?;
    tokio::time::sleep(tokio::time::Duration::from_millis(150)).await;
    app.emit("edit-copy-done", ()).map_err(|e| e.to_string())?;

    let recorder = state.0.lock().map_err(|e| e.to_string())?;
    recorder.start(app.clone())?;
    Ok(())
}

#[tauri::command]
pub async fn complete_edit_flow(
    _app: tauri::AppHandle,
    state: State<'_, RecorderState>,
    original_text: String,
    api_key: String,
    model: String,
) -> Result<String, String> {
    use crate::audio::AudioRecorder;
    use crate::transcription;
    use crate::edit;

    let samples = {
        let recorder = state.0.lock().map_err(|e| e.to_string())?;
        recorder.stop()
    };

    let native_rate = AudioRecorder::native_sample_rate();
    let wav_bytes = AudioRecorder::samples_to_wav(&samples, native_rate);

    let api_url = std::env::var("DICTO_API_URL")
        .unwrap_or_else(|_| "https://dicto.up.railway.app".to_string());

    let transcription = transcription::transcribe(
        wav_bytes, &api_key, "v3-turbo", "auto", &api_url,
    ).await.map_err(|e| format!("{:?}", e))?;

    let result = edit::edit_text(
        &original_text, &transcription.text, &api_key, &model, &api_url,
    ).await.map_err(|e| format!("{:?}", e))?;

    Ok(result.text)
}

#[tauri::command]
pub async fn simulate_paste_cmd() -> Result<(), String> {
    crate::keyboard::simulate_paste()
}

#[tauri::command]
pub async fn simulate_enter_cmd() -> Result<(), String> {
    crate::keyboard::simulate_enter()
}

#[tauri::command]
pub async fn fetch_presets(api_key: String) -> Result<Vec<crate::transform::Preset>, String> {
    let api_url = std::env::var("DICTO_API_URL")
        .unwrap_or_else(|_| "https://dicto.up.railway.app".to_string());
    crate::transform::fetch_presets(&api_key, &api_url).await
}

#[tauri::command]
pub async fn set_always_on_top(app: tauri::AppHandle, value: bool) -> Result<(), String> {
    use tauri::Manager;
    if let Some(win) = app.get_webview_window("main") {
        win.set_always_on_top(value).map_err(|e| e.to_string())?;
    }
    Ok(())
}

#[tauri::command]
pub async fn transform_text(
    text: String,
    prompt: String,
    model: String,
    api_key: String,
    transcription_id: Option<String>,
) -> Result<String, String> {
    let api_url = std::env::var("DICTO_API_URL")
        .unwrap_or_else(|_| "https://dicto.up.railway.app".to_string());
    let result = crate::transform::transform_text(
        &text, &prompt, &model, &api_key,
        transcription_id.as_deref(),
        &api_url,
    ).await?;
    Ok(result.text)
}
