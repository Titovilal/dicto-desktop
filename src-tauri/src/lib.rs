mod audio;
mod transcription;
mod commands;
mod hotkeys;
mod tray;
mod edit;
mod keyboard;
mod transform;

use commands::{start_recording, stop_recording, transcribe_audio, list_audio_devices, register_hotkeys, update_app_status, show_main_window, show_overlay, hide_overlay, start_edit_flow, complete_edit_flow, simulate_paste_cmd, simulate_enter_cmd, fetch_presets, transform_text, set_always_on_top};
use commands::RecorderState;
use audio::AudioRecorder;
use std::sync::Mutex;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .manage(RecorderState(Mutex::new(AudioRecorder::new())))
        .plugin(tauri_plugin_os::init())
        .plugin(tauri_plugin_store::Builder::new().build())
        .plugin(tauri_plugin_global_shortcut::Builder::new().build())
        .plugin(tauri_plugin_clipboard_manager::init())
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_notification::init())
        .setup(|app| {
            tray::setup_tray(app.handle())?;
            let _ = hotkeys::register_hotkeys(
                app.handle(),
                "Ctrl+Shift+Space",
                "Ctrl+Alt+Space",
            );
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            start_recording,
            stop_recording,
            transcribe_audio,
            list_audio_devices,
            register_hotkeys,
            update_app_status,
            show_main_window,
            show_overlay,
            hide_overlay,
            start_edit_flow,
            complete_edit_flow,
            simulate_paste_cmd,
            simulate_enter_cmd,
            fetch_presets,
            transform_text,
            set_always_on_top,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
