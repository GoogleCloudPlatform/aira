import { IUserStore } from '@/interfaces/store';
import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

const initialUserState : Partial<IUserStore> = {
    user: null
}

const useUserStore = create<IUserStore>()(
    devtools(
        persist(
            (set, get) => ({
                user: null,
                getUser: () => get(),
                setUser: (prop : any, newValue: any) => set((state) => ({ ...state, [prop]: newValue })),
                updateUser: (newState : IUserStore) => set(() => ({ ...newState })),
                resetUser: () => set((state) => ({ ...state, ...initialUserState }))
            }),
            {
                name: 'users-storage',
            }
        )
    )
);

export { useUserStore };