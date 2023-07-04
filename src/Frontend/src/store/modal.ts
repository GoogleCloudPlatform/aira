import { IModalStore } from '@/interfaces/store';
import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

const initialModalState : Partial<IModalStore> = {
    open: false,
    title: "",
    icon: { icon: "", classes: "" },
    actions: [],
    message: "",
}

const useModalStore = create<IModalStore>()(
    devtools(
        persist(
            (set, get) => ({
                open: false,
                title: "",
                icon: { icon: "", classes: "" },
                actions: [],
                message: "",
                getModal: () => get(),
                setModal: (prop : any, value: any) => set((state) => ({ ...state, [prop]: value })),
                updateModal: (newState : IModalStore) => set(() => ({ ...newState })),
                resetModal: () => set(() => initialModalState)
            }),
            {
                name: 'modal-storage',
            }
        )
    )
);

export { useModalStore };