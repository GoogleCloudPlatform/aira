import { IRolesStore } from '@/interfaces/store';
import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

const initialRolesState : Partial<IRolesStore> = {
    roles: null,
    role: null,
}

const useRolesStore = create<IRolesStore>()(
    devtools(
        persist(
            (set, get) => ({
                roles: null,
                role: null,
                getRoles: () => get(),
                setRoles: (prop : any, value: any) => set((state) => ({ ...state, [prop]: value })),
                updateRoles: (newState : IRolesStore) => set(() => ({ ...newState })),
                resetRoles: () => set(() => initialRolesState)
            }),
            {
                name: 'roles-storage',
            }
        )
    )
);

export { useRolesStore };