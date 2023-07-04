import { IAction } from "./actions";
import { IExamResponse } from "./exams";
import { IExamsResponse } from "./exams"
import { IInput } from "./form";
import { IGroupResponse, IGroupsResponse } from "./group";
import { IIcon } from "./icons";
import { IOrganizationResponse, IOrganizationsResponse } from "./organization";
import { IQuestion } from "./question";
import { IRoleResponse, IRolesResponse } from "./role";
import { IUserResponse, IUsersResponse } from "./user";

export interface ISettingsStore {
    loading: boolean;
    theme: null;
    menu: boolean;
    getSettings: () => ISettingsStore,
    setSettings: (prop: 'loading' | 'theme' | 'menu', value: any) => void;
    toggleLoading: () => void;
    updateSettings: (newState : ISettingsStore) => void;
    resetSettings: () => void;
}

export interface IExamsStore {
    exams: null | IExamsResponse;
    exam: null | IExamResponse | Array<IQuestion>;
    expanded: boolean;
    questionIndex: number;
    finished: false;
    getExams: () => IExamsStore,
    setExams: (prop: 'exams' | 'exam' | 'questionIndex' | 'finished' | 'expanded', value: any) => void;
    updateExams: (newState : IExamsStore) => void;
    resetExams: () => void;
}

export interface IRecordStore {
    microphonePermission: false;
    state: 'inactive' | 'recording' | 'paused';
    stream: null | MediaStream;
    audioURL: string;
    audioChunks: BlobPart[] | Array<any>;
    canStop: boolean;
    seconds: number,
    getRecord: () => IRecordStore,
    setRecord: (prop: 'microphonePermission' | 'state' | 'stream' | 'audioURL' | 'audioChunks' | 'canStop' | 'seconds', value: any) => void;
    setBlobData: (blobData : any) => void,
    updateRecord: (newState : IRecordStore) => void;    
    resetRecord: () => void;
}

export interface IOrganizationsStore {
    organizations: null | IOrganizationsResponse;
    organization: null | IOrganizationResponse;
    getOrganizations: () => IOrganizationsStore;
    setOrganizations: (prop: 'organizations' | 'organization', value: any) => void;
    updateOrganizations: (newState : IOrganizationsStore) => void; 
    resetOrganizations: () => void;
}

export interface IModalStore {
    open: boolean;
    title: string;
    icon: IIcon;
    actions: Array<IAction>;
    message: string;
    getModal: () => IModalStore;
    setModal: (prop: 'open' | 'title' | 'icon' | 'actions' | 'message', value: any) => void;
    updateModal: (newState : IModalStore) => void; 
    resetModal: () => void;
}

export interface IFormStore {
    inputs: Array<IInput>;
    getForm: () => IFormStore,
    setForm: (prop: 'inputs', value: any) => void;
    updateForm: (newState : IFormStore) => void; 
    resetForm: () => void;
}

export interface IPaginationStore {
    page_size: number;
    page: number;
    query: string;
    getPagination: () => IPaginationStore;
    setPagination: (prop: 'page_size' | 'page' | 'query', value: any) => void;
    updatePagination: (newState : IPaginationStore) => void; 
    resetPagination: () => void;
}

export interface IGroupsStore {
    groups: null | IGroupsResponse;
    group: null | IGroupResponse;
    getGroups: () => IGroupsStore;
    setGroups: (prop: 'groups' | 'group', value: any) => void;
    updateGroups: (newState : IGroupsStore) => void; 
    resetGroups: () => void;
}

export interface IRolesStore {
    roles: null | IRolesResponse;
    role: null | IRoleResponse;
    getRoles: () => IRolesStore;
    setRoles: (prop: 'roles' | 'role', value: any) => void;
    updateRoles: (newState : IRolesStore) => void; 
    resetRoles: () => void;
}

export interface IUsersStore {
    users: null | IUsersResponse;
    user: null | IUserResponse;
    getUsers: () => IUsersStore;
    setUsers: (prop: 'users' | 'user', value: any) => void;
    updateUsers: (newState : IUsersStore) => void; 
    resetUsers: () => void;
}