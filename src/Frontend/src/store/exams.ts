import { IExamsStore } from '@/interfaces/store';
import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

const initialExamsState : Partial<IExamsStore> = {
    expanded: false,
    questionIndex: 0,
    user: null,
    group: undefined
}

const useExamsStore = create<IExamsStore>()(
    devtools(
        persist(
            (set, get) => ({
                expanded: false,
                questionIndex: 0,
                user: null,
                group: undefined,
                getExams: () => get(),
                setExams: (prop : any, value: any) => set((state) => ({ ...state, [prop]: value })),
                updateExams: (newState : IExamsStore) => set(() => ({ ...newState })),
                resetExams: () => set((state) => ({ ...state, ...initialExamsState }))
            }),
            {
                name: 'exams-storage',
            }
        )
    )
);

export { useExamsStore };