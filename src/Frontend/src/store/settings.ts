import { ISettingsStore } from '@/interfaces/store';
import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

const initialSettingsState : Partial<ISettingsStore> | any = {
    loading: false,
    theme: null,
    menu: true,
}

const useSettingsStore = create<ISettingsStore>()(
    devtools(
        persist(
            (set, get) => ({
                ...initialSettingsState,
                getSettings: () => get(),
                setSettings: (prop : any, value: any) => set((state) => ({ ...state, [prop]: value })),
                toggleLoading: () => set((state : any) => ({ loading: !state.loading })),
                updateSettings: (newState : ISettingsStore) => set(() => ({ ...newState })),
                resetSettings: () => set(() => initialSettingsState)
            }),
            {
                name: 'settings-store',
            }
        )
    )
);

export { useSettingsStore };