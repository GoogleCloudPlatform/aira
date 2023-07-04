import { ISettingsStore } from '@/interfaces/store';
import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

const initialSettingsState : Partial<ISettingsStore> = {
    loading: false,
    theme: null,
    menu: false
}

const useSettingsStore = create<ISettingsStore>()(
    devtools(
        persist(
            (set, get) => ({
                loading: false,
                theme: null,
                menu: false,
                getSettings: () => get(),
                setSettings: (prop : any, value: any) => set((state) => ({ ...state, [prop]: value })),
                toggleLoading: () => set((state : any) => ({ loading: !state.loading })),
                updateSettings: (newState : ISettingsStore) => set(() => ({ ...newState })),
                resetSettings: () => set(() => initialSettingsState)
            }),
            {
                name: 'settings-storage',
            }
        )
    )
);

export { useSettingsStore };