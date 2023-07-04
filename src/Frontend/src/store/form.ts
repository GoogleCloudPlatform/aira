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
import { IFormStore } from '@/interfaces/store';
import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

const initialFormState : Partial<IFormStore> = {
    inputs: [],
}

const useFormStore = create<IFormStore>()(
    devtools(
        persist(
            (set, get) => ({
                inputs: [],
                getForm: () => get(),
                setForm: (prop : any, value: any) => set((state) => ({ ...state, [prop]: value })),
                updateForm: (newState : IFormStore) => set(() => ({ ...newState })),
                resetForm: () => set(() => initialFormState)
            }),
            {
                name: 'form-storage',
            }
        )
    )
);

export { useFormStore };