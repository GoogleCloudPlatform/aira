import { ENUM_QUESTION_TYPE_COMPLEX_WORDS, ENUM_QUESTION_TYPE_PHRASES, ENUM_QUESTION_TYPE_WORDS } from '@/constants/enums';
import { ICrudStore } from '@/interfaces/store';
import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

const initialCrudState : Partial<ICrudStore> = {
    exam: {
        name: '',
        questions: [{
            order: 1,
            name: ENUM_QUESTION_TYPE_WORDS,
            type: ENUM_QUESTION_TYPE_WORDS,
            data: '',
            formatted_data: ''
        },
        {
            order: 2,
            name: ENUM_QUESTION_TYPE_COMPLEX_WORDS,
            type: ENUM_QUESTION_TYPE_COMPLEX_WORDS,
            data: '',
            formatted_data: ''
        },
        {
            order: 3,
            name: ENUM_QUESTION_TYPE_PHRASES,
            type: ENUM_QUESTION_TYPE_PHRASES,
            data: '',
            formatted_data: ''
        }
        ],
        grade: '',
        start_date: new Date(),
        end_date: new Date()
    }
}

const useCrudStore = create<ICrudStore>()(
    devtools(
        persist(
            (set, get) => ({
                exam: {
                    name: '',
                    questions: [{
                        order: 1,
                        name: ENUM_QUESTION_TYPE_WORDS,
                        type: ENUM_QUESTION_TYPE_WORDS,
                        data: '',
                        formatted_data: ''
                    },
                    {
                        order: 2,
                        name: ENUM_QUESTION_TYPE_COMPLEX_WORDS,
                        type: ENUM_QUESTION_TYPE_COMPLEX_WORDS,
                        data: '',
                        formatted_data: ''
                    },
                    {
                        order: 3,
                        name: ENUM_QUESTION_TYPE_PHRASES,
                        type: ENUM_QUESTION_TYPE_PHRASES,
                        data: '',
                        formatted_data: ''
                    }
                    ],
                    grade: '',
                    start_date: new Date(),
                    end_date: new Date()
                },
                getCRUD: () => get(),
                setCRUD: (prop : any, value: any) => set((state) => ({ ...state, [prop]: value })),
                updateCRUD: (newState : ICrudStore) => set(() => ({ ...newState })),
                resetCRUD: () => set((state) => ({ ...state, ...initialCrudState }))
            }),
            {
                name: 'crud-storage',
            }
        )
    )
);

export { useCrudStore };