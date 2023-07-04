// Copyright 2022 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     https://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
import { EXAMS, GROUPS, ORGANIZATIONS, ROLES, USERS } from "@/constants/pages";
import { IDependence, IInput } from "@/interfaces/form";
import { IGroupsResponse } from "@/interfaces/group";
import { IOrganizationsResponse } from "@/interfaces/organization";
import { IRolesResponse } from "@/interfaces/role";
import { getGroups } from "@/services/groups";
import { getOrganizations } from "@/services/organization";
import { getRoles } from "@/services/roles";
import { NextRouter } from "next/router";
import { toast } from "react-toastify";
import { i18n } from "next-i18next";
import { IActionTableInfoData } from "@/interfaces/table";
import { ICON_BUILDING_LIBRARY, ICON_DOCUMENT_TEXT, ICON_EXCLAMATION_TRIANGLE, ICON_USER, ICON_USER_GROUP, ICON_X_MARK } from "@/constants/icons";
import { formatInputDate, getFormattedDate } from ".";
import { ENUM_GRADE_OPTIONS, ENUM_ROLE_SCOPES, ENUM_SHIFTS, ENUM_STATE_OPTIONS, ENUM_USER_TYPES, WITH_PASSWORD } from "@/constants/enum";
import { isEmpty } from "lodash";
import { QUESTION_TYPE_PHRASES, QUESTION_TYPE_WORDS } from "@/constants/exam";

export const getBody = (data : any) => {
    try {
        const body : any = {};

        data.forEach((item : IInput) => {
            const { name, value, type, required, render } = item;
    
            //if (!required) return;
    
            const [fieldName, index, key] = name.split("-");
    
            if (type === "array") {
                let newData : any = []            
                value.map((inputs : Array<IInput>, i : number) => {
                    const newValue = getBody(inputs);
                    newData.push(newValue);  
                })
                body[name] = newData;
            } else if (type === "select") {
                let sendKey = key ? key : name;                
                if (sendKey === "organization") sendKey = "organization_id";
                const sendData = Array.isArray(value) ? value.map((i : any) => i.id) : ["groups", "organizations"].includes(item.name) ? [value.id] : value.id; 
                
                body[sendKey] = sendData;
            } else if (type === "date" || type === "datetime-local") {
                const newDate = new Date(value);
                const utcTimestamp = newDate.toUTCString();
                const sendDate = new Date(utcTimestamp).toISOString();
                body[name] = sendDate;
            } else if (fieldName === "user_type") {
                body["type"] = value;
            }else {
                if (key) body[key] = value;
                else body[name] = value;
            }

        });
    
        return body;
    } catch (error) {
        console.error(error);
    }
    
}

export const getField = (router : NextRouter, item : any) : string => {
    const { asPath, locale } = router;

    for (const key in item) {
        const field = item[key];

        if (asPath.includes(ROLES)) {
            if (key === "display_name") {
                const lang = Object.keys(field).find(k => k.includes(locale as string));
                if (!lang) return "";
                return field[lang];
            }
        }    

        if (asPath.includes(GROUPS)) {
            if (key === "organization") {
                return item[key].name;
            }
        }
    }

    return "";
}

export const getFieldByKey = (router : NextRouter, item : any) : string => {
    const { asPath, locale } = router;

    for (const key in item) {
        const field = item[key];

        if (asPath.includes(ROLES)) {
            if (key === "display_name") {
                const lang = Object.keys(field).find(k => k.includes(locale as string));
                if (!lang) return "";
                return field[lang];
            }
        }

        if (asPath.includes(USERS)) {
            if (key === "display_name") {
                const lang = Object.keys(field).find(k => k.includes(locale as string));
                if (!lang) return "";
                return field[lang];
            }
        }

        if (asPath.includes(GROUPS)) {
            if (key === "name") return item[key];
        }
        
        if (asPath.includes(ORGANIZATIONS)) {
            if (key === "name") return item[key];
        }
    }

    return "";
}

export const getFormFields = (router : NextRouter, type : string, scope: string) : Promise<Array<IInput>> => {
    return new Promise<Array<IInput>>(async (resolve, reject) => {
        
        const { asPath, locale } = router;

        if (type.includes(ORGANIZATIONS)) {

            if (scope === 'create') {
                resolve([
                    { name: 'name', value: '', type: 'text', placeholder: 'name', label: 'name', required: true, showLabel: true, render: true },
                    { name: 'city', value: '', type: 'text', placeholder: 'city', label: 'city', required: true, showLabel: true, render: true },
                    { name: 'state', value: '', type: 'select', placeholder: 'state', label: 'state', required: true, showLabel: true, options: [...ENUM_STATE_OPTIONS], defaultOptions: [...ENUM_STATE_OPTIONS], render: true },
                    { name: 'region', value: '', type: 'text', placeholder: 'region', label: 'region', required: true, showLabel: true, render: true },
                ]);
            }

            resolve([
                { name: 'id', value: '', type: 'text', placeholder: 'id', label: 'id', required: false, disabled: true, showLabel: true, render: true },
                { name: 'name', value: '', type: 'text', placeholder: 'name', label: 'name', required: true, showLabel: true, render: true },
                { name: 'city', value: '', type: 'text', placeholder: 'city', label: 'city', required: true, showLabel: true, render: true },
                { name: 'state', value: '', type: 'select', placeholder: 'state', label: 'state', required: true, showLabel: true, options: [...ENUM_STATE_OPTIONS], defaultOptions: [...ENUM_STATE_OPTIONS], render: true },
                { name: 'region', value: '', type: 'text', placeholder: 'region', label: 'region', required: true, showLabel: true, render: true },
                { name: 'created_at', value: '', type: 'datetime-local', placeholder: 'created_at', label: 'created_at', required: false, disabled: true, showLabel: true, render: true },
                { name: 'updated_at', value: '', type: 'datetime-local', placeholder: 'updated_at', label: 'updated_at', required: false, disabled: true, showLabel: true, render: true },
            ]);
        }
    
        if (type.includes(GROUPS)) {
            const organizations : IOrganizationsResponse = await getOrganizations();

            if (!organizations) {
                toast.error(i18n?.t("error_loading_organizations", { ns: "toast" }));
                return resolve([]);
            }

            if (!organizations.items || isEmpty(organizations.items)) {
                toast.warning(i18n?.t("warning_no_organizations", { ns: "toast" }));
            }
            
            if (scope === 'create') {
                resolve([
                    { name: 'name', value: '', type: 'text', placeholder: 'name', label: 'name', required: true, showLabel: true, render: true },
                    { name: 'grade', value: '', type: 'select', placeholder: 'grade', label: 'grade', required: true, showLabel: true,
                        defaultOptions: [...ENUM_GRADE_OPTIONS],
                        options: [...ENUM_GRADE_OPTIONS],
                        render: true
                    },
                    { name: 'shift', value: '', type: 'select', placeholder: 'shift', label: 'shift', required: true, showLabel: true, options: [...ENUM_SHIFTS], render: true },
                    { name: 'organization_id', value: '', type: 'select', placeholder: 'organizations', label: 'organization', required: true, 
                        defaultOptions: [...organizations.items],
                        options: [...organizations.items],
                        showLabel: true,
                        render: true
                    },
                ]);
            }

            
            resolve([
                { name: 'id', value: '', type: 'text', placeholder: 'id', label: 'id', required: false, disabled: true, showLabel: true, render: true },
                { name: 'name', value: '', type: 'text', placeholder: 'name', label: 'name', required: true, showLabel: true, render: true },
                { name: 'organization', value: '', type: 'select', placeholder: 'organizations', label: 'organization', required: true, 
                    defaultOptions: [...organizations.items],
                    options: [...organizations.items],
                    showLabel: true,
                    render: true
                },
                { name: 'grade', value: '', type: 'select', placeholder: 'grade', label: 'grade', required: true, showLabel: true,
                    defaultOptions: [...ENUM_GRADE_OPTIONS],
                    options: [...ENUM_GRADE_OPTIONS],
                    render: true
                },
                { name: 'shift', value: '', type: 'select', placeholder: 'shift', label: 'shift', required: true, showLabel: true, options: [...ENUM_SHIFTS], render: true },
                { name: 'created_at', value: '', type: 'datetime-local', placeholder: 'created_at', label: 'created_at', required: false, disabled: true, showLabel: true, render: true },
                { name: 'updated_at', value: '', type: 'datetime-local', placeholder: 'updated_at', label: 'updated_at', required: false, disabled: true, showLabel: true, render: true },
            ]);
        }

        if (type.includes(ROLES)) {   
            resolve([
                { name: 'id', value: '', type: 'text', placeholder: 'id', label: 'id', required: false, disabled: true, showLabel: true, render: true },
                { name: 'display_name', value: {}, type: 'object', placeholder: 'display_name', label: 'display_name', required: false, disabled: true, options: {}, showLabel: true, render: true },
                { name: 'scopes', value: '', type: 'select', placeholder: 'scopes', label: 'scopes', required: false, disabled: true, multiple: true, 
                    defaultOptions: [...ENUM_ROLE_SCOPES],
                    options: [...ENUM_ROLE_SCOPES], 
                    showLabel: true ,
                    render: true
                },
                { name: 'description', value: {}, type: 'object', placeholder: 'description', label: 'description', required: false, disabled: true, options: {}, showLabel: true, render: true },
                { name: 'created_at', value: '', type: 'datetime-local', placeholder: 'created_at', label: 'created_at', required: false, disabled: true, showLabel: true, render: true },
                { name: 'updated_at', value: '', type: 'datetime-local', placeholder: 'updated_at', label: 'updated_at', required: false, disabled: true, showLabel: true, render: true },
            ])
        }

        if (type.includes(USERS)) {   
            const groups : IGroupsResponse = await getGroups();
            const organizations : IOrganizationsResponse = await getOrganizations();
            const roles : IRolesResponse = await getRoles();
            
            if (!groups) {
                toast.warning(i18n?.t("error_loading_groups", { ns: "toast" }));
                return resolve([]);
            }
            if (!organizations) {
                toast.warning(i18n?.t("error_loading_organizations", { ns: "toast" }));
                return resolve([]);
            }
            if (!roles) {
                toast.warning(i18n?.t("error_loading_roles", { ns: "toast" }));
                return resolve([]);
            }

            if (!groups.items || isEmpty(groups.items)) {
                toast.warning(i18n?.t("warning_no_groups", { ns: "toast" }));
            }

            if (!organizations.items || isEmpty(organizations.items)) {
                toast.warning(i18n?.t("warning_no_organizations", { ns: "toast" }));
            }
            
            if (!roles.items || isEmpty(roles.items)) {
                toast.warning(i18n?.t("warning_no_roles", { ns: "toast" }));
            }

            if (scope === 'create') {
                return resolve([
                    { name: 'user_type', value: '', type: 'radio', placeholder: 'signin_type', label: 'user_type', required: true, showLabel: true, render: true,
                        defaultOptions: [...ENUM_USER_TYPES],
                        options: [...ENUM_USER_TYPES],
                        dependencies: [
                            { key: 'password', condition_values: [WITH_PASSWORD], dynamic: false },
                            { key: 'confirm_password', condition_values: [WITH_PASSWORD], dynamic: false },
                        ]
                    },
                    { name: 'email_address', value: '', type: 'email', placeholder: 'email', label: 'email', required: true, showLabel: true, render: true },
                    { name: 'password', value: '', type: 'password', placeholder: 'password', label: 'password', required: true, showLabel: true, render: true },
                    { name: 'confirm_password', value: '', type: 'password', placeholder: 'confirm_password', label: 'confirm_password', required: true, showLabel: true, render: true },
                    { name: 'name', value: '', type: 'text', placeholder: 'name', label: 'name', required: true, showLabel: true, render: true },
                    { name: 'role_id', value: '', type: 'select', placeholder: 'role', label: 'role', required: true, 
                        defaultOptions: [...roles.items],
                        options: [...roles.items], showLabel: true, render: true, 
                        dependencies: [
                            { key: "groups", condition_values: ["Student", "Teacher", "Alumno", "Profesor", "Aluno", "Professor"], condition_multiple: ["Teacher", "Profesor", "Professor"], dynamic: false },
                            { key: "organizations", condition_values: ["Student", "Teacher", "Alumno", "Profesor", "Aluno", "Professor"], condition_multiple: ["Teacher", "Profesor", "Professor"], dynamic: false },
                        ] 
                    },
                    { name: 'organizations', value: [], type: 'select', placeholder: 'organizations', label: 'organizations', required: false, disabled: true, multiple: true, 
                        defaultOptions: [...organizations.items],
                        options: [...organizations.items], showLabel: true, render: true,
                        dependencies: [
                            { key: "groups", dynamic: true }
                        ]
                    },
                    { name: 'groups', value: [], type: 'select', placeholder: 'groups', label: 'groups', required: false, disabled: true, options: [...groups.items], defaultOptions: [...groups.items], multiple: true, showLabel: true, render: true },
                ]);
            }

            resolve([
                { name: 'id', value: '', type: 'text', placeholder: 'id', label: 'id', required: false, disabled: true, showLabel: true, render: true },
                { name: 'email_address', value: '', type: 'email', placeholder: 'email', label: 'email', required: false, disabled: true, showLabel: true, render: true },
                { name: 'name', value: '', type: 'text', placeholder: 'name', label: 'name', required: true, showLabel: true, render: true },
                { name: 'role_id', value: '', type: 'select', placeholder: 'role', label: 'role', required: false, disabled: true, options: [...roles.items], showLabel: true, render: true,
                    dependencies: [
                        { key: "groups", condition_values: ["Student", "Teacher", "Alumno", "Profesor", "Aluno", "Professor"], condition_multiple: ["Teacher", "Profesor", "Professor"], dynamic: false },
                        { key: "organizations", condition_values: ["Student", "Teacher", "Alumno", "Profesor", "Aluno", "Professor"], condition_multiple: ["Teacher", "Profesor", "Professor"], dynamic: false },
                    ]  
                },
                { name: 'organizations', value: [], type: 'select', placeholder: 'organizations', label: 'organizations', required: true, multiple: true,
                    defaultOptions: [...organizations.items],
                    options: [...organizations.items], showLabel: true, render: true,
                    dependencies: [
                        { key: "groups", dynamic: true }
                    ]
                },
                { name: 'groups', value: [], type: 'select', placeholder: 'groups', label: 'groups', required: true, multiple: true, 
                    defaultOptions: [...groups.items],
                    options: [...groups.items], showLabel: true, render: true 
                },
                { name: 'created_at', value: '', type: 'datetime-local', placeholder: 'created_at', label: 'created_at', required: false, disabled: true, showLabel: true, render: true },
                { name: 'updated_at', value: '', type: 'datetime-local', placeholder: 'updated_at', label: 'updated_at', required: false, disabled: true, showLabel: true, render: true },
            ])
            
        }

        if (type.includes(EXAMS)) {            
            const date = getFormattedDate("en-US", new Date());
            

            if (scope === "create") {
                resolve([
                    { name: 'name', value: '', type: 'text', placeholder: 'name', label: 'name', required: true, showLabel: true, render: true },
                    { name: 'questions', value: [], type: 'array', placeholder: 'questions', label: 'questions', required: true, options: [],
                        fields: [
                            { name: 'questions-0-type', value: '', type: 'select', placeholder: 'type', label: 'type', required: true, classes: 'w-full h-full gap-1 grid grid-flow-row mb-1',
                                options: [
                                    { id: QUESTION_TYPE_WORDS, name: QUESTION_TYPE_WORDS, data: "" },
                                    { id: QUESTION_TYPE_PHRASES, name: QUESTION_TYPE_PHRASES, data: "" },
                                ],
                                render: true
                            },
                            { name: 'questions-0-name', value: '', type: 'text', placeholder: 'name', label: 'name', required: true, classes: 'w-full h-full gap-1 grid grid-flow-row mb-1', render: true },
                            { name: 'questions-0-data', value: '', type: 'text', placeholder: 'data', label: 'data', required: true, classes: 'w-full h-full gap-1 grid grid-flow-row mb-1', render: true },
                        ],
                        showLabel: true,
                        render: true
                    },
                    { name: 'grade', value: '', type: 'select', placeholder: 'grade', label: 'grade', required: true, showLabel: true,
                        options: [...ENUM_GRADE_OPTIONS],
                        render: true
                    },
                    { name: 'start_date', value: formatInputDate(date), type: 'datetime-local', placeholder: 'start_date', label: 'start_date', required: true, showLabel: true, render: true },
                    { name: 'end_date', value: formatInputDate(date), type: 'datetime-local', placeholder: 'end_date', label: 'end_date', required: true, showLabel: true, render: true },
                ]);
            }

            if (scope === 'edit') {
                resolve([
                    { name: 'id', value: '', type: 'text', placeholder: 'id', label: 'id', required: true, disabled: true, showLabel: true, render: true },
                    { name: 'name', value: '', type: 'text', placeholder: 'Name', label: 'name', required: true, showLabel: true, disabled: true, render: true },
                    { name: 'questions', value: [], type: 'array', placeholder: 'Questions', label: 'questions', required: true, options: [], disabled: true,
                        fields: [
                            { name: 'questions-0-type', value: '', type: 'select', placeholder: 'type', label: 'type', required: true, classes: 'w-full h-full gap-1 grid grid-flow-row mb-1',
                                options: [
                                    { id: QUESTION_TYPE_WORDS, name: QUESTION_TYPE_WORDS, data: "", required: true, disabled: true },
                                    { id: QUESTION_TYPE_PHRASES, name: QUESTION_TYPE_PHRASES, data: "", required: true, disabled: true },
                                ],
                                disabled: true
                            },
                            { name: 'questions-0-name', value: '', type: 'text', placeholder: 'Name', label: 'name', required: true, classes: 'w-full h-full gap-1 grid grid-flow-row mb-1', disabled: true },
                            { name: 'questions-0-data', value: '', type: 'text', placeholder: 'Data', label: 'data', required: true, classes: 'w-full h-full gap-1 grid grid-flow-row mb-1', disabled: true },
                        ],
                        showLabel: true,
                        render: true
                    },
                    { name: 'grade', value: '', type: 'select', placeholder: 'grade', label: 'grade', required: true, showLabel: true,
                        options: [...ENUM_GRADE_OPTIONS],
                        disabled: true,
                        render: true
                    },
                    // { name: 'groups', value: [], type: 'select', placeholder: 'Groups', label: 'groups', required: true,
                    //     options: [...groups.items], 
                    //     multiple: true,
                    //     showLabel: true,
                    //     disabled: true
                    // },
                    { name: 'start_date', value: formatInputDate(date), type: 'datetime-local', placeholder: 'start_date', label: 'start_date', required: false, showLabel: true, disabled: true, render: true },
                    { name: 'end_date', value: formatInputDate(date), type: 'datetime-local', placeholder: 'end_date', label: 'end_date', required: false, showLabel: true, disabled: true, render: true },
                    { name: 'created_at', value: '', type: 'datetime-local', placeholder: 'created_at', label: 'created_at', required: false, disabled: true, showLabel: true, render: true },
                    { name: 'updated_at', value: '', type: 'datetime-local', placeholder: 'updated_at', label: 'updated_at', required: false, disabled: true, showLabel: true, render: true },
                ]);
            }
           
            
        }
    
        resolve([]);
    })
}

export const getFilledFormFields = (router : NextRouter, data : any, formFields : Array<IInput>) => {
    try {
        const { asPath, locale } = router;

        let newFormFields : Array<IInput> = Object.assign([], formFields);

        newFormFields.forEach((field) => {
            const { name, type, options, multiple, defaultOptions } = field;
            const entry = Object.entries(data).find(([key]) => key === name);
          
            if (!entry) return;
          
            const [, value] : any = entry;
          
            if (type === "select") {                
                // define input type
                const dependencies = field.dependencies || [];
                dependencies.map((dep : IDependence) => {
                    const dependencyField = newFormFields.find((f) => f.name === dep.key);
                    if (!dependencyField) return;

                    if (dep.condition_values) {
                        let conditionValue = value;

                        const props = options.find((item: any) => item.id === value);
                        if (props.display_name) {
                            conditionValue = props.display_name[locale as string];
                        }

                        const hasDependency = dep.condition_multiple?.includes(conditionValue); 
                        dependencyField.multiple = hasDependency;
                    }
                });

                if (!multiple) {
                    if (!options || !options.length) return;
                    const conditionValue = value.hasOwnProperty("id") ? value.id : value;
                    const props = options.find((item: any) => item.id === conditionValue);
                    field.value = Array.isArray(value) && isEmpty(value) ? value : Array.isArray(value) ? value[0] : { id: value.id, value: value.id, ...props };
                } else if (name === "scopes") {
                    const props = options.find((item: any) => item.id === value[0]);
                    field.value = { ...props };
                } else {
                    const newValues : any = [];
                    value.map((v : any) => {
                        defaultOptions.map((dfo : any) => {
                            if (dfo.id === v.id) newValues.push(dfo);
                        })
                    });
                    field.value = newValues;
                }
            } else if (type === "date" || type === "datetime-local") {
                const formattedDate = formatInputDate(value)//new Date(value).toLocaleDateString();
                field.value = formattedDate;
            } else if (type === "array") {
                const newArray: any[] = value.map((obj: any, index: number) => {
                    const keys = Object.keys(obj);
                    return keys
                        .filter((key) => ["name", "data", "type"].includes(key))
                        .map((key) => {
                            let options: any[] = [];
                            if (key === "type") {
                                options = [
                                    { id: QUESTION_TYPE_WORDS, name: QUESTION_TYPE_WORDS, data: "", required: true },
                                    { id: QUESTION_TYPE_PHRASES, name: QUESTION_TYPE_PHRASES, data: "", require: true },
                                ];
                            }
                            return {
                                name: `questions-${index}-${key}`,
                                value: key === "type" ? { id: obj[key], name: obj[key] } : obj[key],
                                type: key === "type" ? "select" : "text",
                                options,
                                required: field.required,
                                disabled: field.disabled,
                                render: field.render,
                            };
                        });
                });
                field.value = newArray;
            } else {
                field.value = value;
            }

         
            const dependencies = field.dependencies || [];
            dependencies.map((dep : IDependence) => {
                const dependencyField = newFormFields.find((f) => f.name === dep.key);
                if (!dependencyField) return;

                if (dep.dynamic) {
                    if (isEmpty(dependencyField.options) || isEmpty(field.value)) return;
                    const conditionValue = Array.isArray(field.value) ? field.value : field.value.id;
                    let newOptions : any = [];
                    if (Array.isArray(field.value)) {
                        field.value.map((v) => {
                            return dependencyField.defaultOptions.map((o : any) => {
                                if (o["organization"].id === v.id) newOptions.push(o);
                            });
                        });
                    } else {
                        newOptions = dependencyField.defaultOptions.filter((option : any) => option["organization"].id === conditionValue)
                    }
                    
                    dependencyField.options = newOptions;
                }

                if (dep.condition_values) {
                    let conditionValue = field.value;
                    
                    if (field.value.display_name) {
                        conditionValue = field.value.display_name[locale as string];
                    }
      
                    const hasDependency = dep.condition_values?.includes(conditionValue) ? true : false;
                    dependencyField.render = hasDependency;
                    dependencyField.required = hasDependency;
                    //dependencyField.multiple = dep.condition_multiple?.includes(conditionValue)
                }
            })
       
            
        });

        
          
      
        return newFormFields;
    } catch(err) {
        toast.error(i18n?.t("error_loading_form", { ns: "toast" }));
        return [];
    }
}

export const getModalInfo = (type : string) : IActionTableInfoData | {} => {
    if (type.includes(ORGANIZATIONS)) {
        return {
            create: {
                title: i18n?.t("create_organization"),
                message: "",
                icon: { icon: ICON_BUILDING_LIBRARY, classes: "text-blue-600 bg-blue-100" }
            },
            edit: {
                title: i18n?.t("edit_organization"),
                message: "",
                icon: { icon: ICON_BUILDING_LIBRARY, classes: "text-blue-600 bg-blue-100" }
            },
            delete: {
                title: i18n?.t("delete_organization"),
                message: i18n?.t("confirm_delete_organization"),
                icon: { icon: ICON_EXCLAMATION_TRIANGLE, classes: "text-red-600 bg-red-100" }
            },
        }
    }

    if (type.includes(GROUPS)) {
        return {
            create: {
                title: i18n?.t("create_group"),
                message: "",
                icon: { icon: ICON_USER_GROUP, classes: "text-blue-600 bg-blue-100" }
            },
            edit: {
                title: i18n?.t("edit_group"),
                message: "",
                icon: { icon: ICON_USER_GROUP, classes: "text-blue-600 bg-blue-100" }
            },
            delete: {
                title: i18n?.t("delete_group"),
                message: i18n?.t("confirm_delete_group"),
                icon: { icon: ICON_EXCLAMATION_TRIANGLE, classes: "text-red-600 bg-red-100" }
            },
        }
    }

    if (type.includes(ROLES)) {
        return {
            create: {
                title: i18n?.t("create_role"),
                message: "",
                icon: { icon: ICON_USER, classes: "text-blue-600 bg-blue-100" }
            },
            edit: {
                title: i18n?.t("view_role"),
                message: "",
                icon: { icon: ICON_USER, classes: "text-blue-600 bg-blue-100" }
            },
            delete: {
                title: i18n?.t("delete_role"),
                message: i18n?.t("confirm_delete_role"),
                icon: { icon: ICON_EXCLAMATION_TRIANGLE, classes: "text-red-600 bg-red-100" }
            },
        }
    }

    if (type.includes(EXAMS)) {
        return {
            create: {
                title: i18n?.t("create_exam"),
                message: "",
                icon: { icon: ICON_DOCUMENT_TEXT, classes: "text-blue-600 bg-blue-100" }
            },
            edit: {
                title: i18n?.t("view_exam"),
                message: "",
                icon: { icon: ICON_DOCUMENT_TEXT, classes: "text-blue-600 bg-blue-100" }
            },
            delete: {
                title: i18n?.t("delete_exam"),
                message: i18n?.t("confirm_delete_exam"),
                icon: { icon: ICON_EXCLAMATION_TRIANGLE, classes: "text-red-600 bg-red-100" }
            },
        }
    }

    if (type.includes(USERS)) {
        return {
            create: {
                title: i18n?.t("create_user"),
                message: "",
                icon: { icon: ICON_USER, classes: "text-blue-600 bg-blue-100" }
            },
            edit: {
                title: i18n?.t("edit_user"),
                message: "",
                icon: { icon: ICON_USER, classes: "text-blue-600 bg-blue-100" }
            },
            delete: {
                title: i18n?.t("delete_user"),
                message: i18n?.t("confirm_delete_user"),
                icon: { icon: ICON_EXCLAMATION_TRIANGLE, classes: "text-red-600 bg-red-100" }
            },
        }
    }

    return {
        create: {
            title: i18n?.t("no_title"),
            message: i18n?.t("no_message"),
            icon: { icon: ICON_X_MARK, classes: "text-blue-600 bg-blue-100" }
        },
        edit: {
            title: i18n?.t("no_title"),
            message: i18n?.t("no_message"),
            icon: { icon: ICON_X_MARK, classes: "text-blue-600 bg-blue-100" }
        },
        delete: {
            title: i18n?.t("no_title"),
            message: i18n?.t("no_message"),
            icon: { icon: ICON_X_MARK, classes: "text-red-600 bg-red-100" }
        },
    };
}