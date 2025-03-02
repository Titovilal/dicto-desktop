interface Window {
    popupAPI?: {
        onUpdateState: (callback: (state: 'recording' | 'processing' | 'finished') => void) => void;
    };
} 