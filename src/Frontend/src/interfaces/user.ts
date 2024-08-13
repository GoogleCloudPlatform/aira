import { IExam } from './exam';
import { IGroup } from './group';
import { IOrganization } from './organization';

//export interface IUser {}

export interface IUsersResponse {
  items: Array<IUserResponse>;
  pages: number;
  current_page: number;
  total: number;
}

export interface IUserResponse {
  id: string;
  name: string;
  exams: Array<IExam>
}

export interface IProfileResponse {
  county: string | null;
  created_at: string;
  email_address: string;
  external_id: string | null;
  id: string;
  last_login: string;
  name: string;
  region: string | null;
  role_id: string;
  state: string | null;
  updated_at: string;
  groups: Array<IGroup>;
  organizations: Array<IOrganization>;
}

export interface IUserExportResponse {
  url: string;
}

export interface IUsersImportResponse {}

export interface IUserExamsResponse {
  items: Array<IExam>;
  pages: number;
  current_page: number;
  total: number;
}
