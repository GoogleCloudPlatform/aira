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