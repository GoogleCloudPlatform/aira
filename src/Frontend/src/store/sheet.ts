import { ISheetStore } from '@/interfaces/store';
import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

const initialSheetState : Partial<ISheetStore> | any = {
    options: {}
}

const useSheetStore = create<ISheetStore>()(
    devtools(
        persist(
            (set, get) => ({
                ...initialSheetState,
                getSheet: () => get(),
                setSheet: (prop : any, value: any) => set((state) => ({ ...state, [prop]: value })),
                updateSheet: (newState : ISheetStore) => set(() => ({ ...newState })),
                resetSheet: () => set(() => initialSheetState)
            }),
            {
                name: 'sheet-store',
            }
        )
    )
);

export { useSheetStore };