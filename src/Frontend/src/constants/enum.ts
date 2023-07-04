import { SCOPE_ADMIN, SCOPE_EDUCATOR, SCOPE_LEARNER } from "./rbac";

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
    { id: "AC", name: "Acre", value: "AC" },
    { id: "AL", name: "Alagoas", value: "AL" },
    { id: "AP", name: "Amapá", value: "AP" },
    { id: "AM", name: "Amazonas", value: "AM" },
    { id: "BA", name: "Bahia", value: "BA" },
    { id: "CE", name: "Ceará", value: "CE" },
    { id: "DF", name: "Distrito Federal", value: "DF" },
    { id: "ES", name: "Espírito Santo", value: "ES" },
    { id: "GO", name: "Goiás", value: "GO" },
    { id: "MA", name: "Maranhão", value: "MA" },
    { id: "MT", name: "Mato Grosso", value: "MT" },
    { id: "MS", name: "Mato Grosso do Sul", value: "MS" },
    { id: "MG", name: "Minas Gerais", value: "MG" },
    { id: "PA", name: "Pará", value: "PA" },
    { id: "PB", name: "Paraíba", value: "PB" },
    { id: "PR", name: "Paraná", value: "PR" },
    { id: "PE", name: "Pernambuco", value: "PE" },
    { id: "PI", name: "Piauí", value: "PI" },
    { id: "RJ", name: "Rio de Janeiro", value: "RJ" },
    { id: "RN", name: "Rio Grande do Norte", value: "RN" },
    { id: "RS", name: "Rio Grande do Sul", value: "RS" },
    { id: "RO", name: "Rondônia", value: "RO" },
    { id: "RR", name: "Roraima", value: "RR" },
    { id: "SC", name: "Santa Catarina", value: "SC" },
    { id: "SP", name: "São Paulo", value: "SP" },
    { id: "SE", name: "Sergipe", value: "SE" },
    { id: "TO", name: "Tocantins", value: "TO" }
];

export const ENUM_SHIFTS = [
    { id: "morning", name: "morning", value: "morning" },
    { id: "evening", name: "evening", value: "evening" },
    { id: "night", name: "night", value: "night" }
];


export const GOOGLE_SIGNIN = 'firebase';
export const WITH_PASSWORD = 'password';
export const ENUM_USER_TYPES = [
    { id: GOOGLE_SIGNIN, name: "google_signin", value: GOOGLE_SIGNIN },
    { id: WITH_PASSWORD, name: "with_password", value: WITH_PASSWORD },
]

export const ENUM_ROLE_SCOPES = [
    { id: SCOPE_ADMIN, name: SCOPE_ADMIN, value: SCOPE_ADMIN },
    { id: SCOPE_LEARNER, name: SCOPE_LEARNER, value: SCOPE_LEARNER }, 
    { id: SCOPE_EDUCATOR, name: SCOPE_EDUCATOR, value: SCOPE_EDUCATOR }, 
]

  
  
  
  