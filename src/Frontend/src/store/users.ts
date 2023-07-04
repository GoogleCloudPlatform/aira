import { IUsersStore } from '@/interfaces/store';
import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

const initialUsersState : Partial<IUsersStore> = {
    users: null,
    user: null,
}

const useUsersStore = create<IUsersStore>()(
    devtools(
        persist(
            (set, get) => ({
                users: null,
                user: null,
                getUsers: () => get(),
                setUsers: (prop : any, value: any) => set((state) => ({ ...state, [prop]: value })),
                updateUsers: (newState : IUsersStore) => set(() => ({ ...newState })),
                resetUsers: () => set(() => initialUsersState)
            }),
            {
                name: 'users-storage',
            }
        )
    )
);

export { useUsersStore };