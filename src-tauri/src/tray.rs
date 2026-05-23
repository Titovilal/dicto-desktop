use tauri::{
    menu::{MenuBuilder, MenuItemBuilder},
    tray::TrayIconBuilder,
    AppHandle, Emitter, Manager,
};

pub fn setup_tray(app: &AppHandle) -> Result<(), Box<dyn std::error::Error>> {
    let open_item = MenuItemBuilder::with_id("open", "Abrir Dicto").build(app)?;
    let record_item = MenuItemBuilder::with_id("record", "Grabar").build(app)?;
    let quit_item = MenuItemBuilder::with_id("quit", "Salir").build(app)?;

    let menu = MenuBuilder::new(app)
        .item(&open_item)
        .item(&record_item)
        .separator()
        .item(&quit_item)
        .build()?;

    let mut builder = TrayIconBuilder::with_id("main-tray")
        .tooltip("Dicto — Listo")
        .menu(&menu);

    if let Some(icon) = app.default_window_icon() {
        builder = builder.icon(icon.clone());
    }

    builder
        .on_menu_event(|app, event| match event.id().as_ref() {
            "open" => {
                if let Some(window) = app.get_webview_window("main") {
                    let _ = window.show();
                    let _ = window.set_focus();
                }
            }
            "record" => {
                let _ = app.emit("tray-record", ());
            }
            "quit" => {
                app.exit(0);
            }
            _ => {}
        })
        .build(app)?;

    Ok(())
}

pub fn update_tray_status(app: &AppHandle, status: &str) {
    let tooltip = match status {
        "idle" => "Dicto — Listo",
        "recording" => "Dicto — Grabando...",
        "processing" => "Dicto — Procesando...",
        "success" => "Dicto — Transcripción completada",
        "error" => "Dicto — Error",
        _ => "Dicto",
    };

    if let Some(tray) = app.tray_by_id("main-tray") {
        let _ = tray.set_tooltip(Some(tooltip));
    }
}
