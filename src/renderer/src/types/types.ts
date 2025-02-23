export interface Profile {
    name: string;
    prompt: string;
    useAI: boolean;
    copyToClipboard: boolean;
    language: string;
    returnBoth: boolean;
    autoPaste: boolean;
    modelName: string;
    temperature: number;
    transcriptionPrompt: string;
}

export interface User {
    email: string;
    name: string;
    sub_credits: number;
    otp_credits: number;
    sub_date_time: string | null;
    otp_date_time: string | null;
    has_subscription: boolean;
    cancel_next_month: boolean;
}

export interface StoreSchema {
    settings: {
        theme: 'light' | 'dark';
        appLanguage: string;
        soundEnabled: boolean;
        soundVolume: number;
        recordShortcut: string;
        selectedProfile: string;
        apiKey: string;
    };
    profiles: Profile[];
    user: User;
}