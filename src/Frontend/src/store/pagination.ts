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
import { PAGE_SIZE } from '@/constants/pagination';
import { IPaginationStore } from '@/interfaces/store';
import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

const initialPaginationState : Partial<IPaginationStore> = {
    page_size: PAGE_SIZE,
    page: 1,
    query: ""
}

const usePaginationStore = create<IPaginationStore>()(
    devtools(
        persist(
            (set, get) => ({
                page_size: PAGE_SIZE,
                page: 1,
                query: "",
                getPagination: () => get(),
                setPagination: (prop : any, newValue: any) => set((state) => ({ ...state, [prop]: newValue })),
                updatePagination: (newState : IPaginationStore) => set(() => ({ ...newState })),
                resetPagination: () => set(() => initialPaginationState)
            }),
            {
                name: 'pagination-storage',
            }
        )
    )
);

export { usePaginationStore };