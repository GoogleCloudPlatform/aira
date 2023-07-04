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
import { IExamsStore } from '@/interfaces/store';
import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

const initialExamsState : Partial<IExamsStore> = {
    exams: null,
    exam: null,
    expanded: false,
    questionIndex: 0,
    finished: false,
}

const useExamsStore = create<IExamsStore>()(
    devtools(
        persist(
            (set, get) => ({
                exams: null,
                exam: null,
                expanded: false,
                questionIndex: 0,
                finished: false,
                getExams: () => get(),
                setExams: (prop : any, value: any) => set((state) => ({ ...state, [prop]: value })),
                updateExams: (newState : IExamsStore) => set(() => ({ ...newState })),
                resetExams: () => set(() => initialExamsState)
            }),
            {
                name: 'exams-storage',
            }
        )
    )
);

export { useExamsStore };