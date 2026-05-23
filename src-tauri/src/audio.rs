use cpal::traits::{DeviceTrait, HostTrait, StreamTrait};
use std::sync::{Arc, Mutex};
use tauri::{AppHandle, Emitter};

#[derive(serde::Serialize, Clone)]
struct AudioLevelPayload {
    level: f32,
}

pub struct AudioRecorder {
    recording: Arc<Mutex<bool>>,
    samples: Arc<Mutex<Vec<f32>>>,
}

impl AudioRecorder {
    pub fn new() -> Self {
        AudioRecorder {
            recording: Arc::new(Mutex::new(false)),
            samples: Arc::new(Mutex::new(Vec::new())),
        }
    }

    pub fn start(&self, app: AppHandle) -> Result<(), String> {
        {
            let mut rec = self.recording.lock().map_err(|e| e.to_string())?;
            *rec = true;
        }
        {
            let mut s = self.samples.lock().map_err(|e| e.to_string())?;
            s.clear();
        }

        let recording = Arc::clone(&self.recording);
        let samples = Arc::clone(&self.samples);

        std::thread::spawn(move || {
            let host = cpal::default_host();
            let device = match host.default_input_device() {
                Some(d) => d,
                None => {
                    eprintln!("No input device found");
                    return;
                }
            };

            let config = match device.default_input_config() {
                Ok(c) => c,
                Err(e) => {
                    eprintln!("Could not get default input config: {}", e);
                    return;
                }
            };

            let sample_rate = config.sample_rate().0;
            let channels = config.channels() as usize;

            let samples_clone = Arc::clone(&samples);
            let recording_clone = Arc::clone(&recording);

            // Level emit timing
            let level_samples: Arc<Mutex<Vec<f32>>> = Arc::new(Mutex::new(Vec::new()));
            let level_samples_clone = Arc::clone(&level_samples);
            let app_clone = app.clone();
            let recording_for_level = Arc::clone(&recording);

            // Spawn a thread to emit audio levels periodically
            std::thread::spawn(move || {
                loop {
                    std::thread::sleep(std::time::Duration::from_millis(50));
                    {
                        let rec = recording_for_level.lock().unwrap();
                        if !*rec {
                            break;
                        }
                    }
                    let chunk: Vec<f32> = {
                        let mut lv = level_samples_clone.lock().unwrap();
                        let c = lv.clone();
                        lv.clear();
                        c
                    };
                    if !chunk.is_empty() {
                        let rms = (chunk.iter().map(|s| s * s).sum::<f32>() / chunk.len() as f32).sqrt();
                        let level = (rms * 10.0).min(1.0);
                        let _ = app_clone.emit("audio-level", AudioLevelPayload { level });
                    }
                }
            });

            let level_samples_for_stream = Arc::clone(&level_samples);

            let stream_result = match config.sample_format() {
                cpal::SampleFormat::F32 => {
                    device.build_input_stream(
                        &config.into(),
                        move |data: &[f32], _| {
                            let is_rec = *recording_clone.lock().unwrap();
                            if !is_rec {
                                return;
                            }
                            let mono: Vec<f32> = data
                                .chunks(channels)
                                .map(|ch| ch.iter().sum::<f32>() / ch.len() as f32)
                                .collect();
                            samples_clone.lock().unwrap().extend_from_slice(&mono);
                            level_samples_for_stream.lock().unwrap().extend_from_slice(&mono);
                        },
                        |err| eprintln!("Stream error: {}", err),
                        None,
                    )
                }
                cpal::SampleFormat::I16 => {
                    device.build_input_stream(
                        &config.into(),
                        move |data: &[i16], _| {
                            let is_rec = *recording_clone.lock().unwrap();
                            if !is_rec {
                                return;
                            }
                            let mono: Vec<f32> = data
                                .chunks(channels)
                                .map(|ch| {
                                    let sum: f32 = ch.iter().map(|s| *s as f32 / 32768.0).sum();
                                    sum / ch.len() as f32
                                })
                                .collect();
                            samples_clone.lock().unwrap().extend_from_slice(&mono);
                            level_samples_for_stream.lock().unwrap().extend_from_slice(&mono);
                        },
                        |err| eprintln!("Stream error: {}", err),
                        None,
                    )
                }
                cpal::SampleFormat::U16 => {
                    device.build_input_stream(
                        &config.into(),
                        move |data: &[u16], _| {
                            let is_rec = *recording_clone.lock().unwrap();
                            if !is_rec {
                                return;
                            }
                            let mono: Vec<f32> = data
                                .chunks(channels)
                                .map(|ch| {
                                    let sum: f32 = ch.iter().map(|s| (*s as f32 - 32768.0) / 32768.0).sum();
                                    sum / ch.len() as f32
                                })
                                .collect();
                            samples_clone.lock().unwrap().extend_from_slice(&mono);
                            level_samples_for_stream.lock().unwrap().extend_from_slice(&mono);
                        },
                        |err| eprintln!("Stream error: {}", err),
                        None,
                    )
                }
                fmt => {
                    eprintln!("Unsupported sample format: {:?}", fmt);
                    return;
                }
            };

            let stream = match stream_result {
                Ok(s) => s,
                Err(e) => {
                    eprintln!("Failed to build stream: {}", e);
                    return;
                }
            };

            if let Err(e) = stream.play() {
                eprintln!("Failed to play stream: {}", e);
                return;
            }

            // Keep stream alive while recording
            loop {
                std::thread::sleep(std::time::Duration::from_millis(100));
                let is_rec = *recording.lock().unwrap();
                if !is_rec {
                    break;
                }
            }

            // stream dropped here, recording stops
            let _ = app.emit("audio-level", AudioLevelPayload { level: 0.0 });
            eprintln!("Recording thread exiting, native sample rate: {}", sample_rate);
        });

        Ok(())
    }

    pub fn stop(&self) -> Vec<f32> {
        if let Ok(mut rec) = self.recording.lock() {
            *rec = false;
        }
        std::thread::sleep(std::time::Duration::from_millis(150));
        if let Ok(s) = self.samples.lock() {
            s.clone()
        } else {
            Vec::new()
        }
    }

    /// Resample from `src_rate` to 16000 Hz using linear interpolation, then encode as WAV.
    pub fn samples_to_wav(samples: &[f32], src_rate: u32) -> Vec<u8> {
        const TARGET_RATE: u32 = 16000;

        let resampled: Vec<f32> = if src_rate == TARGET_RATE {
            samples.to_vec()
        } else {
            let ratio = src_rate as f64 / TARGET_RATE as f64;
            let out_len = (samples.len() as f64 / ratio) as usize;
            (0..out_len)
                .map(|i| {
                    let pos = i as f64 * ratio;
                    let idx = pos as usize;
                    let frac = (pos - idx as f64) as f32;
                    let a = samples.get(idx).copied().unwrap_or(0.0);
                    let b = samples.get(idx + 1).copied().unwrap_or(0.0);
                    a + (b - a) * frac
                })
                .collect()
        };

        encode_wav_vec(&resampled, TARGET_RATE)
    }

    pub fn list_devices() -> Vec<String> {
        let host = cpal::default_host();
        match host.input_devices() {
            Ok(devices) => devices
                .filter_map(|d| d.name().ok())
                .collect(),
            Err(e) => {
                eprintln!("Failed to list devices: {}", e);
                Vec::new()
            }
        }
    }

    /// Returns the native sample rate of the default input device, or 44100 as fallback.
    pub fn native_sample_rate() -> u32 {
        let host = cpal::default_host();
        if let Some(device) = host.default_input_device() {
            if let Ok(config) = device.default_input_config() {
                return config.sample_rate().0;
            }
        }
        44100
    }
}

fn encode_wav_vec(samples: &[f32], sample_rate: u32) -> Vec<u8> {
    // Build a PCM WAV in memory manually (no file I/O needed)
    let num_samples = samples.len() as u32;
    let num_channels: u16 = 1;
    let bits_per_sample: u16 = 16;
    let byte_rate = sample_rate * num_channels as u32 * (bits_per_sample as u32 / 8);
    let block_align = num_channels * (bits_per_sample / 8);
    let data_size = num_samples * 2; // 2 bytes per i16 sample
    let chunk_size = 36 + data_size;

    let mut buf: Vec<u8> = Vec::with_capacity((44 + data_size) as usize);

    // RIFF header
    buf.extend_from_slice(b"RIFF");
    buf.extend_from_slice(&chunk_size.to_le_bytes());
    buf.extend_from_slice(b"WAVE");

    // fmt chunk
    buf.extend_from_slice(b"fmt ");
    buf.extend_from_slice(&16u32.to_le_bytes()); // subchunk1 size
    buf.extend_from_slice(&1u16.to_le_bytes());  // PCM = 1
    buf.extend_from_slice(&num_channels.to_le_bytes());
    buf.extend_from_slice(&sample_rate.to_le_bytes());
    buf.extend_from_slice(&byte_rate.to_le_bytes());
    buf.extend_from_slice(&block_align.to_le_bytes());
    buf.extend_from_slice(&bits_per_sample.to_le_bytes());

    // data chunk
    buf.extend_from_slice(b"data");
    buf.extend_from_slice(&data_size.to_le_bytes());
    for s in samples {
        let v = (s.clamp(-1.0, 1.0) * i16::MAX as f32) as i16;
        buf.extend_from_slice(&v.to_le_bytes());
    }

    buf
}
