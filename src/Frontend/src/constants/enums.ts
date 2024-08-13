import { SCOPE_ADMIN, SCOPE_EDUCATOR, SCOPE_USER } from "./rbac";

export const FIRST_ELEMENTARY_SCHOOL = '1º Ano';
export const SECOND_ELEMENTARY_SCHOOL = '2º Ano';
export const THIRD_ELEMENTARY_SCHOOL = '3º Ano';
export const FOURTH_ELEMENTARY_SCHOOL = '4º Ano';
export const FIFTH_ELEMENTARY_SCHOOL = '5º Ano';
export const SIXTH_ELEMENTARY_SCHOOL = '6º Ano';
export const SEVENTH_ELEMENTARY_SCHOOL = '7º Ano';
export const EIGHTH_ELEMENTARY_SCHOOL = '8º Ano';
export const NINTH_ELEMENTARY_SCHOOL = '9º Ano';

export const FIRST_HIGH_SCHOOL = '1ª Série';
export const SECOND_HIGH_SCHOOL = '2ª Série';
export const THIRD_HIGH_SCHOOL = '3ª Série';

export const ENUM_GRADE = [
    FIRST_ELEMENTARY_SCHOOL,
    SECOND_ELEMENTARY_SCHOOL,
    THIRD_ELEMENTARY_SCHOOL,
    FOURTH_ELEMENTARY_SCHOOL,
    FIFTH_ELEMENTARY_SCHOOL,
    SIXTH_ELEMENTARY_SCHOOL,
    SEVENTH_ELEMENTARY_SCHOOL,
    EIGHTH_ELEMENTARY_SCHOOL,
    NINTH_ELEMENTARY_SCHOOL,
    FIRST_HIGH_SCHOOL,
    SECOND_HIGH_SCHOOL,
    THIRD_HIGH_SCHOOL,
];

export const ENUM_GRADE_OPTIONS = [
    { id: FIRST_ELEMENTARY_SCHOOL, name: FIRST_ELEMENTARY_SCHOOL, value: FIRST_ELEMENTARY_SCHOOL },
    { id: SECOND_ELEMENTARY_SCHOOL, name: SECOND_ELEMENTARY_SCHOOL, value: SECOND_ELEMENTARY_SCHOOL },
    { id: THIRD_ELEMENTARY_SCHOOL, name: THIRD_ELEMENTARY_SCHOOL, value: THIRD_ELEMENTARY_SCHOOL },
    { id: FOURTH_ELEMENTARY_SCHOOL, name: FOURTH_ELEMENTARY_SCHOOL, value: FOURTH_ELEMENTARY_SCHOOL },
    { id: FIFTH_ELEMENTARY_SCHOOL, name: FIFTH_ELEMENTARY_SCHOOL, value: FIFTH_ELEMENTARY_SCHOOL },
    { id: SIXTH_ELEMENTARY_SCHOOL, name: SIXTH_ELEMENTARY_SCHOOL, value: SIXTH_ELEMENTARY_SCHOOL },
    { id: SEVENTH_ELEMENTARY_SCHOOL, name: SEVENTH_ELEMENTARY_SCHOOL, value: SEVENTH_ELEMENTARY_SCHOOL },
    { id: EIGHTH_ELEMENTARY_SCHOOL, name: EIGHTH_ELEMENTARY_SCHOOL, value: EIGHTH_ELEMENTARY_SCHOOL },
    { id: NINTH_ELEMENTARY_SCHOOL, name: NINTH_ELEMENTARY_SCHOOL, value: NINTH_ELEMENTARY_SCHOOL },
    { id: FIRST_HIGH_SCHOOL, name: FIRST_HIGH_SCHOOL, value: FIRST_HIGH_SCHOOL },
    { id: SECOND_HIGH_SCHOOL, name: SECOND_HIGH_SCHOOL, value: SECOND_HIGH_SCHOOL },
    { id: THIRD_HIGH_SCHOOL, name: THIRD_HIGH_SCHOOL, value: THIRD_HIGH_SCHOOL },
];

export const ENUM_STATE_OPTIONS = [
    { id: "AC", label: "Acre", value: "AC" },
    { id: "AL", label: "Alagoas", value: "AL" },
    { id: "AP", label: "Amapá", value: "AP" },
    { id: "AM", label: "Amazonas", value: "AM" },
    { id: "BA", label: "Bahia", value: "BA" },
    { id: "CE", label: "Ceará", value: "CE" },
    { id: "DF", label: "Distrito Federal", value: "DF" },
    { id: "ES", label: "Espírito Santo", value: "ES" },
    { id: "GO", label: "Goiás", value: "GO" },
    { id: "MA", label: "Maranhão", value: "MA" },
    { id: "MT", label: "Mato Grosso", value: "MT" },
    { id: "MS", label: "Mato Grosso do Sul", value: "MS" },
    { id: "MG", label: "Minas Gerais", value: "MG" },
    { id: "PA", label: "Pará", value: "PA" },
    { id: "PB", label: "Paraíba", value: "PB" },
    { id: "PR", label: "Paraná", value: "PR" },
    { id: "PE", label: "Pernambuco", value: "PE" },
    { id: "PI", label: "Piauí", value: "PI" },
    { id: "RJ", label: "Rio de Janeiro", value: "RJ" },
    { id: "RN", label: "Rio Grande do Norte", value: "RN" },
    { id: "RS", label: "Rio Grande do Sul", value: "RS" },
    { id: "RO", label: "Rondônia", value: "RO" },
    { id: "RR", label: "Roraima", value: "RR" },
    { id: "SC", label: "Santa Catarina", value: "SC" },
    { id: "SP", label: "São Paulo", value: "SP" },
    { id: "SE", label: "Sergipe", value: "SE" },
    { id: "TO", label: "Tocantins", value: "TO" }
];

export const ENUM_SHIFTS = [
    { id: "morning", name: "morning", value: "morning" },
    { id: "evening", name: "evening", value: "evening" },
    { id: "night", name: "night", value: "night" },
    { id: "allday", name: "allday", value: "allday" }
];

export const GOOGLE_SIGNIN = 'firebase';
export const WITH_PASSWORD = 'password';
export const ENUM_USER_TYPES = [
    { id: WITH_PASSWORD, label: "with_password", value: WITH_PASSWORD },
    { id: GOOGLE_SIGNIN, label: "google_signin", value: GOOGLE_SIGNIN },
]

export const ENUM_ROLE_SCOPES = [
    { id: SCOPE_ADMIN, label: SCOPE_ADMIN, value: SCOPE_ADMIN },
    { id: SCOPE_USER, label: SCOPE_USER, value: SCOPE_USER }, 
    { id: SCOPE_EDUCATOR, label: SCOPE_EDUCATOR, value: SCOPE_EDUCATOR }, 
]

export const ENUM_IMPORT_TYPES = {
    user: "USER",
    organization: "ORGANIZATION",
    group: "GROUP"
}

export const ENUM_USERS_IMPORT = [
    { label: "customer_id", value: "customer_id" },
    { label: "name", value: "name" },
    { label: "email_address", value: "email_address" },
    { label: "password", value: "password" },
    { label: "groups", value: "groups" },
    { label: "organizations", value: "organizations" },
    { label: "role_id", value: "role_id" },
    { label: "region", value: "region" },
    { label: "county", value: "county" },
    { label: "state", value: "state" }
];

export const ENUM_GROUPS_IMPORT = [
    { label: "customer_id", value: "value" },
    { label: "name", value: "name" },
    { label: "grade", value: "grade" },
    { label: "shift", value: "shift" },
    { label: "organization", value: "organization" }
];

export const ENUM_ORGANIZATIONS_IMPORT = [
    { label: "customer_id", value: "customer_id" },
    { label: "name", value: "name" },
    { label: "region", value: "region" },
    { label: "city", value: "city" },
    { label: "county", value: "county" },
    { label: "state", value: "state" }
];

export const ENUM_EXAM_STATUS_FINISHED = 'FINISHED';
export const ENUM_EXAM_STATUS_NOT_STARTED = 'NOT_STARTED';
export const ENUM_EXAM_STATUS_IN_PROGRESS = 'IN_PROGRESS';
export const ENUM_QUESTION_STATUS_FINISHED = 'FINISHED';
export const ENUM_QUESTION_STATUS_IN_PROGRESS = 'in_progress';
export const ENUM_QUESTION_STATUS_NOT_STARTED = 'not_started';

export const ENUM_QUESTION_TYPE_WORDS = 'words';
export const ENUM_QUESTION_TYPE_COMPLEX_WORDS = 'complex_words';
export const ENUM_QUESTION_TYPE_PHRASES = 'phrases';
export const ENUM_QUESTION_TYPE_MULTIPLE_CHOICE = 'multiple_choice';

export const ENUM_NO_RATING = "no_classification";
export const ENUM_FLUENT = "fluent";
export const ENUM_READER = "reader";
export const ENUM_PRE_READER_ONE = "pre_reader_one";
export const ENUM_PRE_READER_TWO = "pre_reader_two";
export const ENUM_PRE_READER_THREE = "pre_reader_three";
export const ENUM_PRE_READER_FOUR = "pre_reader_four";

export const ENUM_ACCEPTED_FILE_TYPES = ['csv'];
