use tauri::{AppHandle, Emitter, Manager};
use tauri_plugin_global_shortcut::GlobalShortcutExt;

pub fn register_hotkeys(app: &AppHandle, record_hotkey: &str, edit_hotkey: &str) -> Result<(), String> {
    // Unregister all existing shortcuts first
    let _ = app.global_shortcut().unregister_all();

    // Register record hotkey
    let record_key = record_hotkey.to_string();
    let app_clone = app.clone();
    app.global_shortcut()
        .on_shortcut(record_hotkey, move |_app, _shortcut, event| {
            use tauri_plugin_global_shortcut::ShortcutState;
            if event.state == ShortcutState::Pressed {
                let _ = app_clone.emit("hotkey-record", ());
            }
        })
        .map_err(|e| format!("Failed to register record hotkey '{}': {}", record_key, e))?;

    // Register edit hotkey
    let edit_key = edit_hotkey.to_string();
    let app_clone2 = app.clone();
    app.global_shortcut()
        .on_shortcut(edit_hotkey, move |_app, _shortcut, event| {
            use tauri_plugin_global_shortcut::ShortcutState;
            if event.state == ShortcutState::Pressed {
                let _ = app_clone2.emit("hotkey-edit", ());
            }
        })
        .map_err(|e| format!("Failed to register edit hotkey '{}': {}", edit_key, e))?;

    Ok(())
}

pub fn unregister_all(app: &AppHandle) -> Result<(), String> {
    app.global_shortcut()
        .unregister_all()
        .map_err(|e| e.to_string())
}
