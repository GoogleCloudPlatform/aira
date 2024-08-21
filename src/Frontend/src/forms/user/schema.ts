import { MAX_FILE_SIZE } from "@/constants";
import { ENUM_STATE_OPTIONS, ENUM_USERS_IMPORT, GOOGLE_SIGNIN, WITH_PASSWORD } from "@/constants/enums";
import { TOption } from "@/interfaces/form";
import { getOptions } from "@/utils/form";
import { isEmpty } from "lodash";
import { z } from "zod";

export const OptionSchema = z.object({
    value: z.string(),
    label: z.string()
})

let roles : TOption[] | null = null;

const ROLE_ADMIN_ARRAY = ["Administrator", "Administrador"];
const ROLE_STATE_MANAGER_ARRAY = ["State Manager", "Gerente Estatal", "Gestor Estadual"];
const ROLE_REGIONAL_MANAGER_ARRAY = ["Regional Education Manager", "Gerente Regional de Educacíon", "Gestor da Regional de Educação"];
const ROLE_COUNTY_MANAGER_ARRAY = ["County Manager", "Gerente municipal", "Gestor de Município"];
const ROLE_SCHOOL_MANAGER_ARRAY = ["School Manager", "Director de Escuela", "Gestor de Escola"];
const ROLE_STUDENT_ARRAY = ["Student", "Alumno", "Aluno"];
const ROLE_PROFESSOR_ARRAY = ["Teacher", "Profesor", "Professor"];

export const SchemaCreateUserPasswordForm = z.object({
    type: z.literal(WITH_PASSWORD),
    //user_type: z.string().min(1, { message: "toast.errors.form.required_field" }),
    name: z.string().min(1, { message: "toast.errors.form.required_field" }),
    email_address: z.string().min(1, { message: "toast.errors.form.required_field" }).email("toast.errors.form.invalid_email"),
    password: z.string().min(5, { message: "toast.errors.form.min_password" }).max(50, { message: "toast.errors.form.max_password" }),
    confirm_password: z.string().min(5, { message: "toast.errors.form.min_password" }).max(50, { message: "toast.errors.form.max_password" }),
    role_id: z.string().min(1, { message: "toast.errors.form.required_field" }),
    organizations: z.union([z.array(z.string()), z.array(OptionSchema)]).optional().transform(organizations => {
        if (!organizations || isEmpty(organizations)) return undefined;

        const data : string[] = organizations.map(o => typeof o === 'string' ? o : o.value);
        return data;
    }),
    groups: z.union([z.array(z.string()), z.array(OptionSchema)]).optional().transform(groups => {
        if (!groups || isEmpty(groups)) return undefined;

        const data : string[] = groups.map(o => typeof o === 'string' ? o : o.value);
        return data;
    }),
    state: z.string().optional().transform(state => {
        if (!state || isEmpty(state)) return undefined;

        return state;
    }),
    county: z.string().optional().transform(county => {
        if (!county || isEmpty(county)) return undefined;

        return county;
    }),
    region: z.string().optional().transform(region => {
        if (!region || isEmpty(region)) return undefined;

        return region;
    })
}).superRefine(async ({ type, confirm_password, password, role_id, organizations, groups, state, county, region }, ctx) => {
    if (!roles) {
        roles = await getOptions("roles");
    }
    
    const roleItem = roles.find(role => role.id === role_id);
    if (roleItem) {
        if (ROLE_PROFESSOR_ARRAY.includes(roleItem.label) || ROLE_STUDENT_ARRAY.includes(roleItem.label)) {
            if (isEmpty(organizations)) {
                ctx.addIssue({
                    code: "custom",
                    message: "toast.errors.form.required_field",
                    path: ["organizations"],
                });
            }
            if (!isEmpty(organizations) && isEmpty(groups)) {
                ctx.addIssue({
                    code: "custom",
                    message: "toast.errors.form.required_field",
                    path: ["groups"],
                });
            }
            if (isEmpty(groups)) {
                ctx.addIssue({
                    code: "custom",
                    message: "toast.errors.form.required_field",
                    path: ["groups"],
                });
            }
        }     

        if (ROLE_SCHOOL_MANAGER_ARRAY.includes(roleItem.label)) {
            if (isEmpty(organizations)) {
                ctx.addIssue({
                    code: "custom",
                    message: "toast.errors.form.required_field",
                    path: ["organizations"],
                });
            }           
        }           

        if (ROLE_COUNTY_MANAGER_ARRAY.includes(roleItem.label)) {
            if (isEmpty(county)) {
                ctx.addIssue({
                    code: "custom",
                    message: "toast.errors.form.required_field",
                    path: ["county"],
                });
            }           
        }           

        if (ROLE_REGIONAL_MANAGER_ARRAY.includes(roleItem.label)) {
            if (isEmpty(region)) {
                ctx.addIssue({
                    code: "custom",
                    message: "toast.errors.form.required_field",
                    path: ["region"],
                });
            }           
        }           

        if (ROLE_STATE_MANAGER_ARRAY.includes(roleItem.label)) {
            if (isEmpty(state)) {
                ctx.addIssue({
                    code: "custom",
                    message: "toast.errors.form.required_field",
                    path: ["state"],
                });
            } else {
                const state = (value: string) => ENUM_STATE_OPTIONS.some(option => option.value === value)
                if (!state) {
                    ctx.addIssue({
                        code: "custom",
                        message: "toast.errors.form.invalid_state",
                        path: ["state"],
                    });
                }
            }       
        }           
    }
    if (type === WITH_PASSWORD && confirm_password !== password) {
        ctx.addIssue({
            code: "custom",
            message: "toast.errors.form.password_didnt_match",
            path: ["confirm_password"],
        });
    }
});

export const SchemaCreateUserFirebaseForm = z.object({
    type: z.literal(GOOGLE_SIGNIN),
    //user_type: z.string().min(1, { message: "toast.errors.form.required_field" }),
    name: z.string().min(1, { message: "toast.errors.form.required_field" }),
    email_address: z.string().min(1, { message: "toast.errors.form.required_field" }).email("toast.errors.form_invalid_email"),
    role_id: z.string().min(1, { message: "toast.errors.form.required_field" }),
    organizations: z.union([z.array(z.string()), z.array(OptionSchema)]).optional().transform(organizations => {
        if (!organizations || isEmpty(organizations)) return undefined;

        const data : string[] = organizations.map(o => typeof o === 'string' ? o : o.value);
        return data;
    }),
    groups: z.union([z.array(z.string()), z.array(OptionSchema)]).optional().transform(groups => {
        if (!groups || isEmpty(groups)) return undefined;

        const data : string[] = groups.map(o => typeof o === 'string' ? o : o.value);
        return data;
    }),
    state: z.string().optional().transform(state => {
        if (!state || isEmpty(state)) return undefined;

        return state;
    }),
    county: z.string().optional().transform(county => {
        if (!county || isEmpty(county)) return undefined;

        return county;
    }),
    region: z.string().optional().transform(region => {
        if (!region || isEmpty(region)) return undefined;

        return region;
    })
}).superRefine(async ({ role_id, organizations, groups, county, state, region }, ctx) => {
    if (!roles) {
        roles = await getOptions("roles");
    }

    const roleItem = roles.find(role => role.id === role_id);
    if (roleItem) {
        if (ROLE_PROFESSOR_ARRAY.includes(roleItem.label) || ROLE_STUDENT_ARRAY.includes(roleItem.label)) {
            if (isEmpty(organizations)) {
                ctx.addIssue({
                    code: "custom",
                    message: "toast.errors.form.required_field",
                    path: ["organizations"],
                });
            }
            if (!isEmpty(organizations) && isEmpty(groups)) {
                ctx.addIssue({
                    code: "custom",
                    message: "toast.errors.form.required_field",
                    path: ["groups"],
                });
            }
            if (isEmpty(groups)) {
                ctx.addIssue({
                    code: "custom",
                    message: "toast.errors.form.required_field",
                    path: ["groups"],
                });
            }
        }     

        if (ROLE_SCHOOL_MANAGER_ARRAY.includes(roleItem.label)) {
            if (isEmpty(organizations)) {
                ctx.addIssue({
                    code: "custom",
                    message: "toast.errors.form.required_field",
                    path: ["organizations"],
                });
            }           
        }           

        if (ROLE_COUNTY_MANAGER_ARRAY.includes(roleItem.label)) {
            if (isEmpty(county)) {
                ctx.addIssue({
                    code: "custom",
                    message: "toast.errors.form.required_field",
                    path: ["county"],
                });
            }           
        }           

        if (ROLE_REGIONAL_MANAGER_ARRAY.includes(roleItem.label)) {
            if (isEmpty(region)) {
                ctx.addIssue({
                    code: "custom",
                    message: "toast.errors.form.required_field",
                    path: ["region"],
                });
            }           
        }           

        if (ROLE_STATE_MANAGER_ARRAY.includes(roleItem.label)) {
            if (isEmpty(state)) {
                ctx.addIssue({
                    code: "custom",
                    message: "toast.errors.form.required_field",
                    path: ["state"],
                });
            } else {
                const state = (value: string) => ENUM_STATE_OPTIONS.some(option => option.value === value)
                if (!state) {
                    ctx.addIssue({
                        code: "custom",
                        message: "toast.errors.form.invalid_state",
                        path: ["state"],
                    });
                }
            }       
        }           
    }
});

export const SchemaCreateUserForm = z.union([SchemaCreateUserPasswordForm, SchemaCreateUserFirebaseForm]);//FormSchemaCreateUserPassword.or(FormSchemaCreateUserFirebase);

export const SchemaEditUserForm = z.object({
    id: z.string().uuid(),
    email_address: z.string().min(1, { message: "toast.errors.form.required_field" }).email("toast.errors.form_invalid_email"),
    name: z.string(),
    role_id: z.string(),
    organizations: z.union([z.array(z.string()), z.array(OptionSchema)]).nullable().transform(organizations => {
        if (!organizations || isEmpty(organizations)) return undefined;

        const data : string[] = organizations.map(o => typeof o === 'string' ? o : o.value);
        return data;
    }),
    groups: z.union([z.array(z.string()), z.array(OptionSchema)]).nullable().transform(groups => {
        if (!groups || isEmpty(groups)) return undefined;

        const data : string[] = groups.map(g => typeof g === 'string' ? g : g.value);
        return data;
    }),
    state: z.string().nullable().transform(state => {
        if (!state || isEmpty(state)) return undefined;

        return state;
    }),
    county: z.string().nullable().transform(county => {
        if (!county || isEmpty(county)) return undefined;

        return county;
    }),
    region: z.string().nullable().transform(region => {
        if (!region || isEmpty(region)) return undefined;

        return region;
    })
}).superRefine(async ({ role_id, organizations, groups, county, state, region }, ctx) => {
    if (!roles) {
        roles = await getOptions("roles");
    }

    const roleItem = roles.find(role => role.id === role_id);
    if (roleItem) {
        if (ROLE_PROFESSOR_ARRAY.includes(roleItem.label) || ROLE_STUDENT_ARRAY.includes(roleItem.label)) {
            if (isEmpty(organizations)) {
                ctx.addIssue({
                    code: "custom",
                    message: "toast.errors.form.required_field",
                    path: ["organizations"],
                });
            }
            if (!isEmpty(organizations) && isEmpty(groups)) {
                ctx.addIssue({
                    code: "custom",
                    message: "toast.errors.form.required_field",
                    path: ["groups"],
                });
            }
            if (isEmpty(groups)) {
                ctx.addIssue({
                    code: "custom",
                    message: "toast.errors.form.required_field",
                    path: ["groups"],
                });
            }
        }     

        if (ROLE_SCHOOL_MANAGER_ARRAY.includes(roleItem.label)) {
            if (isEmpty(organizations)) {
                ctx.addIssue({
                    code: "custom",
                    message: "toast.errors.form.required_field",
                    path: ["organizations"],
                });
            }           
        }           

        if (ROLE_COUNTY_MANAGER_ARRAY.includes(roleItem.label)) {
            if (isEmpty(county)) {
                ctx.addIssue({
                    code: "custom",
                    message: "toast.errors.form.required_field",
                    path: ["county"],
                });
            }           
        }           

        if (ROLE_REGIONAL_MANAGER_ARRAY.includes(roleItem.label)) {
            if (isEmpty(region)) {
                ctx.addIssue({
                    code: "custom",
                    message: "toast.errors.form.required_field",
                    path: ["region"],
                });
            }           
        }           

        if (ROLE_STATE_MANAGER_ARRAY.includes(roleItem.label)) {
            if (isEmpty(state)) {
                ctx.addIssue({
                    code: "custom",
                    message: "toast.errors.form.required_field",
                    path: ["state"],
                });
            } else {
                const state = (value: string) => ENUM_STATE_OPTIONS.some(option => option.value === value)
                if (!state) {
                    ctx.addIssue({
                        code: "custom",
                        message: "toast.errors.form.invalid_state",
                        path: ["state"],
                    });
                }
            }       
        }           
    }
});

export const SchemaImportUser = z.object({
    file: typeof window === 'undefined' ? z.any() : z.instanceof(FileList).optional(),
    keys: z.array(z.object({
        type: z.string().refine(value => ENUM_USERS_IMPORT.some(option => option.value === value), {
            message: "toast.errors.form.invalid_key",
        }),
        data: z.string()
    }))
}).superRefine(({ file }, ctx) => {
    if (isEmpty(file)) {
        ctx.addIssue({
            code: "custom",
            message: "toast.errors.form.file_required",
            path: ["file"],
        })
    }

    if (file && !isEmpty(file) && !["text/csv"].includes(file[0].type)) {
        ctx.addIssue({
            code: "custom",
            message: "toast.errors.form.file_csv",
            path: ["file"],
        })
    }

    if (file && !isEmpty(file) && file[0].size > MAX_FILE_SIZE) {
        ctx.addIssue({
            code: "custom",
            message: "toast.errors.form.file_max_size_5",
            path: ["file"],
        })
    }
});


export const SchemaCreateUserDefaultValues : z.infer<typeof SchemaCreateUserForm> = {
    type: WITH_PASSWORD,
    name: '',
    email_address: '',
    password: '',
    confirm_password: '',
    role_id: '',
    organizations: [],
    groups: [],
    state: '',
    region: '',
    county: '',
}

export const SchemaEditUserDefaultValues : z.infer<typeof SchemaEditUserForm> & { id: string, email_address: string, role_id: string } = {
    id: '',
    name: '',
    email_address: '',
    role_id: '',
    organizations: [],
    groups: [],
    state: '',
    region: '',
    county: '',
}

export const SchemaImportUserDefaultValues : z.infer<typeof SchemaImportUser> = {
    file: undefined,
    keys: ENUM_USERS_IMPORT.map(item => ({
        type: item.value,
        data: ''
    }))
}