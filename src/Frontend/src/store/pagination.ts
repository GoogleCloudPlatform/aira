import { PAGE_SIZE } from '@/constants/paginations';
import { IPaginationStore } from '@/interfaces/store';
import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

const initialPaginationState : Partial<IPaginationStore> = {
    page_size: PAGE_SIZE,
    page: 1,
    query: "",
    show_finished: false
}

const usePaginationStore = create<IPaginationStore>()(
    devtools(
        persist(
            (set, get) => ({
                page_size: PAGE_SIZE,
                page: 1,
                query: "",
                show_finished: false,
                getPagination: () => get(),
                setPagination: (prop : any, newValue: any) => set((state) => ({ ...state, [prop]: newValue })),
                updatePagination: (newState : IPaginationStore) => set(() => ({ ...newState })),
                resetPagination: () => set((state) => ({ ...state, ...initialPaginationState }))
            }),
            {
                name: 'pagination-storage',
            }
        )
    )
);

export { usePaginationStore };