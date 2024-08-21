export const ROLE_ADMIN = "admin";

// general scopes
export const SCOPE_ADMIN = "admin";
export const SCOPE_EDUCATOR = "semi-admin";
export const SCOPE_USER = "user";

// looker scopes
export const SCOPE_USER_VIEWER = "user.viewer";
export const SCOPE_DASHBOARD_VIEWER = "dashboard.viewer";
export const SCOPE_GROUP_VIEWER = "group.viewer";

// scopes
export const SCOPE_USER_IMPERSONATE = "user.impersonate";
export const SCOPE_ORGANIZATION_LIST = "organization.list";
export const SCOPE_GROUP_LIST = "group.list";
export const SCOPE_USER_LIST = "user.list";
export const SCOPE_EXAM_LIST = "exam.list";

// rbac provider scopes - new scopes should be added here
export const SCOPES : Array<string> = [
    SCOPE_ADMIN, SCOPE_EDUCATOR, SCOPE_USER,
    SCOPE_USER_VIEWER, SCOPE_DASHBOARD_VIEWER, SCOPE_GROUP_VIEWER,
    SCOPE_USER_IMPERSONATE,
    SCOPE_ORGANIZATION_LIST,
    SCOPE_GROUP_LIST,
    SCOPE_USER_LIST,
    SCOPE_EXAM_LIST
];

export const ROLE_ADMIN_ARRAY = ["Administrator", "Administrador"];
export const ROLE_STATE_MANAGER_ARRAY = ["State Manager", "Gerente Estatal", "Gestor Estadual"];
export const ROLE_REGIONAL_MANAGER_ARRAY = ["Regional Education Manager", "Gerente Regional de Educacíon", "Gestor da Regional de Educação"];
export const ROLE_COUNTY_MANAGER_ARRAY = ["County Manager", "Gerente municipal", "Gestor de Município"];
export const ROLE_SCHOOL_MANAGER_ARRAY = ["School Manager", "Director de Escuela", "Gestor de Escola"];
export const ROLE_STUDENT_ARRAY = ["Student", "Alumno", "Aluno"];
export const ROLE_PROFESSOR_ARRAY = ["Teacher", "Profesor", "Professor"];