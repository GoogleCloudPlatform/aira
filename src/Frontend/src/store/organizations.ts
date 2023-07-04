import { IOrganizationsStore } from '@/interfaces/store';
import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

const initialOrganiationsState : Partial<IOrganizationsStore> = {
    organizations: null,
    organization: null,
}

const useOrganizationsStore = create<IOrganizationsStore>()(
    devtools(
        persist(
            (set, get) => ({
                organizations: null,
                organization: null,
                getOrganizations: () => get(),
                setOrganizations: (prop : any, value: any) => set((state) => ({ ...state, [prop]: value })),
                updateOrganizations: (newState : IOrganizationsStore) => set(() => ({ ...newState })),
                resetOrganizations: () => set(() => initialOrganiationsState)
            }),
            {
                name: 'organizations-storage',
            }
        )
    )
);

export { useOrganizationsStore };