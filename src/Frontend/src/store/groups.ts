import { IGroupsStore } from '@/interfaces/store';
import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

const initialGroupsState : Partial<IGroupsStore> = {
    groups: null,
    group: null,
}

const useGroupsStore = create<IGroupsStore>()(
    devtools(
        persist(
            (set, get) => ({
                groups: null,
                group: null,
                getGroups: () => get(),
                setGroups: (prop : any, value: any) => set((state) => ({ ...state, [prop]: value })),
                updateGroups: (newState : IGroupsStore) => set(() => ({ ...newState })),
                resetGroups: () => set(() => initialGroupsState)
            }),
            {
                name: 'groups-storage',
            }
        )
    )
);

export { useGroupsStore };