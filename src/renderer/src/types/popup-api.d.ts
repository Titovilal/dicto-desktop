interface Window {
    popupAPI?: {
        onUpdateState: (callback: (state: 'recording' | 'processing' | 'finished' | 'using') => void) => () => void;
        onUpdateMessage?: (callback: (message: string) => void) => () => void;
    };
} 