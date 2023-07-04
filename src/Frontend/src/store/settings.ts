// Copyright 2022 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     https://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
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