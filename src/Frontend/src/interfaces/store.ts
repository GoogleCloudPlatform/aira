import { IUser } from "./auth";

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

export interface ISheetStore {
    options: any;
    getSheet: () => ISheetStore,
    setSheet: (prop: 'options', value: any) => void;
    updateSheet: (newState : ISheetStore) => void;
    resetSheet: () => void;
}

export interface IPaginationStore {
    page_size: number;
    page: number;
    query: string;
    show_finished: boolean;
    getPagination: () => IPaginationStore;
    setPagination: (prop: keyof IPaginationStore, value: any) => void;
    updatePagination: (newState : IPaginationStore) => void; 
    resetPagination: () => void;
}

export interface IUserStore {
    user: null | Partial<IUser>;
    getUser: () => IUserStore;
    setUser: (prop: keyof IUserStore, value: any) => void;
    updateUser: (newState : IUserStore) => void; 
    resetUser: () => void;
}

export interface IExamsStore {
    expanded: boolean;
    questionIndex: number;
    user?: null | IUser;
    group?: string;
    getExams: () => IExamsStore,
    setExams: (prop: 'questionIndex' | 'expanded' | 'user' | 'group', value: any) => void;
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
    examID: string;
    getRecord: () => IRecordStore,
    setRecord: (prop: 'microphonePermission' | 'state' | 'stream' | 'audioURL' | 'audioChunks' | 'canStop' | 'seconds' | 'examID', value: any) => void;
    setBlobData: (blobData : any) => void,
    updateRecord: (newState : IRecordStore) => void;    
    resetRecord: () => void;
}

export interface ICrudStore {
    exam: {
        name:string;
        questions: Array<{
            order: number,
            name: string,
            type: string,
            data: string,
            formatted_data: string
        }>;
        grade:string;
        start_date: Date;
        end_date: Date;
    }
    getCRUD: () => ICrudStore,
    setCRUD: (prop: 'exam' , value: any) => void;
    updateCRUD: (newState : ICrudStore) => void;
    resetCRUD: () => void;
}