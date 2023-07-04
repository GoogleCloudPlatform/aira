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
import { IRecordStore } from '@/interfaces/store';
import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

const initialRecordState : Partial<IRecordStore> = {
    microphonePermission: false,
    state: 'inactive',
    stream: null,
    audioURL: '',
    audioChunks: [],
    canStop: false,
    seconds: 60,
}

const useRecordStore = create<IRecordStore>()(
    devtools(
        persist(
            (set, get) => ({
                microphonePermission: false,
                state: 'inactive',
                stream: null,
                audioURL: '',
                audioChunks: [],
                canStop: false,
                seconds: 60,
                getRecord: () => get(),
                setRecord: (prop : any, value: any) => set((state) => ({ ...state, [prop]: value })),
                setBlobData: (audioData : any) => {
                    const reader = new FileReader();

                    reader.onloadend = () => {
                        const base64Data: string | ArrayBuffer | null = reader.result;
                        if (typeof base64Data === 'string') {
                            localStorage.setItem('audioData', base64Data);
                        }
                    };
    
                    reader.readAsDataURL(audioData);
                },
                updateRecord: (newState : IRecordStore) => set(() => ({ ...newState })),
                resetRecord: () => set(() => initialRecordState)
            }),
            {
                name: 'record-storage',
            }
        )
    )
);

export { useRecordStore };