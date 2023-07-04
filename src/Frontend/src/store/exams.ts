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