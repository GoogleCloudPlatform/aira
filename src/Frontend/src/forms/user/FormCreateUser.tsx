import { SchemaCreateUserDefaultValues } from "@/forms/user/schema";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Button } from "@/components/ui/button";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Input } from "@/components/ui/input";
import { PasswordInput } from "@/components/ui/extensions/password-input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { mapToOptionType } from "@/utils/form";
import { useCallback, useEffect, useState } from "react";
import { TOption } from "@/interfaces/form";
import { isEmpty } from "lodash";
import MultipleSelector from "@/components/ui/extensions/multiple-select";
import { createUser } from "@/services/user";
import { ENUM_USER_TYPES, WITH_PASSWORD } from "@/constants/enums";
import { TFormCreateProps } from "@/interfaces/component";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { IRolesResponse } from "@/interfaces/roles";
import { getAllRoles } from "@/services/role";
import { getAllOrganizations, getOrganizationsUtils } from "@/services/organization";
import { getAllGroups } from "@/services/group";
import { CATEGORY_GROUPS, CATEGORY_ORGANIZATIONS, CATEGORY_ORGANIZATIONS_UTILS, CATEGORY_ROLES, CATEGORY_USERS } from "@/constants";
import { IOrganizationsResponse, IOrganizationsUtilsResponse } from "@/interfaces/organization";
import { IGroupsResponse } from "@/interfaces/group";
import SkeletonSheet from "@/components/skeletons/SkeletonSheet";
import { useTranslations } from "next-intl";
import { ROLE_ADMIN_ARRAY, ROLE_COUNTY_MANAGER_ARRAY, ROLE_PROFESSOR_ARRAY, ROLE_REGIONAL_MANAGER_ARRAY, ROLE_SCHOOL_MANAGER_ARRAY, ROLE_STATE_MANAGER_ARRAY, ROLE_STUDENT_ARRAY } from "@/constants/rbac";
import { toast } from "react-toastify";
import { useLoading } from "@/context/loading";
import Loading from "@/components/loading/Loading";

type TDefaultOptions = {
    type: Array<TOption>;
    role_id: Array<TOption>;
    organizations: Array<TOption>;
    groups: Array<TOption>;
    organizations_utils: IOrganizationsUtilsResponse,
}

const initialDefaultOptions: TDefaultOptions = {
    type: ENUM_USER_TYPES,
    role_id: [],
    organizations: [],
    groups: [],
    organizations_utils: { state: [], county: [], region: [] },
}

const FormCreateUser: React.FC<TFormCreateProps> = ({ setOpen, formData }) => {
    const [defaultOptions, setDefaultOptions] = useState<TDefaultOptions>(initialDefaultOptions);
    const { loading, setLoading } = useLoading()
    
    const t = useTranslations();
    const queryClient = useQueryClient();

    const { data: rolesOptions, isLoading: isLoadingRoles } = useQuery<IRolesResponse>({ queryKey: [CATEGORY_ROLES], queryFn: getAllRoles });
    const { data: organizationsOptions, isLoading: isLoadingOrganizations } = useQuery<IOrganizationsResponse>({ queryKey: [CATEGORY_ORGANIZATIONS], queryFn: getAllOrganizations });
    const { data: groupsOptions, isLoading: isLoadingGroups } = useQuery<IGroupsResponse>({ queryKey: [CATEGORY_GROUPS], queryFn: getAllGroups });
    const { data: organizationUtilsOptions, isLoading: isLoadingOrganizationUtils } = useQuery<IOrganizationsUtilsResponse>({ queryKey: [CATEGORY_ORGANIZATIONS_UTILS], queryFn: getOrganizationsUtils });

    useEffect(() => {
        const getDataOptions = async () => {
            if (!rolesOptions || !organizationsOptions || !groupsOptions || !organizationUtilsOptions) return;
            const userTypeOptions = ENUM_USER_TYPES;
            setDefaultOptions({
                type: userTypeOptions,
                role_id: mapToOptionType(rolesOptions),
                organizations: mapToOptionType(organizationsOptions),
                groups: mapToOptionType(groupsOptions),
                organizations_utils: organizationUtilsOptions
            });
        }
    
        getDataOptions();
    }, [rolesOptions, organizationsOptions, groupsOptions, organizationUtilsOptions]);

    const form = useForm<z.infer<typeof formData.schema>>({
        resolver: zodResolver(formData.schema),
        defaultValues: formData.defaultValues || SchemaCreateUserDefaultValues
    });

    const [type, role_id, organizations, groups] = form.watch(['type', 'role_id', 'organizations', 'groups']);

    const isAdminRole = useCallback(() => {
        if (isEmpty(defaultOptions.role_id)) return false;
        const roleItem = defaultOptions.role_id.find(role => role.id === role_id);
        if (!roleItem) return false;

        if (ROLE_ADMIN_ARRAY.includes(roleItem.label)) return true;

        return false;
    }, [defaultOptions, role_id]);

    const isStateManagerRole = useCallback(() => {
        if (isEmpty(defaultOptions.role_id)) return false;
        const roleItem = defaultOptions.role_id.find(role => role.id === role_id);
        if (!roleItem) return false;

        if (ROLE_STATE_MANAGER_ARRAY.includes(roleItem.label)) return true;

        return false;
    }, [defaultOptions, role_id]);

    const isRegionManagerRole = useCallback(() => {
        if (isEmpty(defaultOptions.role_id)) return false;
        const roleItem = defaultOptions.role_id.find(role => role.id === role_id);
        if (!roleItem) return false;

        if (ROLE_REGIONAL_MANAGER_ARRAY.includes(roleItem.label)) return true;

        return false;
    }, [defaultOptions, role_id]);

    const isCountyManagerRole = useCallback(() => {
        if (isEmpty(defaultOptions.role_id)) return false;
        const roleItem = defaultOptions.role_id.find(role => role.id === role_id);
        if (!roleItem) return false;

        if (ROLE_COUNTY_MANAGER_ARRAY.includes(roleItem.label)) return true;

        return false;
    }, [defaultOptions, role_id]);

    const isSchoolManagerRole = useCallback(() => {
        if (isEmpty(defaultOptions.role_id)) return false;
        const roleItem = defaultOptions.role_id.find(role => role.id === role_id);
        if (!roleItem) return false;

        if (ROLE_SCHOOL_MANAGER_ARRAY.includes(roleItem.label)) return true;

        return false;
    }, [defaultOptions, role_id]);

    const isStudentRole = useCallback((): boolean => {
        if (isEmpty(defaultOptions.role_id)) return false;
        const roleItem = defaultOptions.role_id.find(role => role.id === role_id);
        if (!roleItem) return false;

        if (ROLE_STUDENT_ARRAY.includes(roleItem.label)) return true;

        return false;
    }, [defaultOptions, role_id]);


    useEffect(() => {
        if (isEmpty(role_id)) {
            form.unregister(['organizations', 'groups', 'state', 'region', 'county'])
        }
    }, [role_id, form])

    const onSubmit = async (values: z.infer<typeof formData.schema>) => {
        setLoading(true)
        try {
            await createUser(values);
            toast.success(t('toast.success.form.user_created'))
            setOpen(false)
        } catch (error: any) {
            if (error.response.status === 409) {
                toast.error(t('toast.errors.form.already_exists'))
            } else {
                toast.error(t('toast.errors.form.create_user'))
            }
        } finally {
            setLoading(false)
        }
        queryClient.invalidateQueries({ queryKey: [CATEGORY_USERS] });
    }

    const getOrganizationsOptions = useCallback(() => {
        if (isEmpty(role_id) || isAdminRole() || !organizations) return [];

        let newOrganizationOptions : TOption[] = Object.assign([], defaultOptions['organizations']);

        if (isStudentRole()) {
            newOrganizationOptions = newOrganizationOptions.map((organization: TOption)=> ({
                ...organization,
                disable: organizations.some((org : any) => org.value !== organization.value)
            }));
            return newOrganizationOptions;
        }

        return newOrganizationOptions;
    }, [role_id, isAdminRole, defaultOptions, isStudentRole, organizations]);

    const getGroupsOptions = useCallback(() => {
        if (isEmpty(role_id) || isAdminRole() || !organizations || isEmpty(organizations)) return [];

        let newGroupsOptions : TOption[] = Object.assign([], defaultOptions['groups']);
        
        newGroupsOptions = organizations.flatMap((organization: any) => {
            return defaultOptions['groups'].filter((option : any) => option.organization.id === organization.id);
        });

        if (isStudentRole()) {
            newGroupsOptions = newGroupsOptions.map((group) => ({
                ...group,
                disable: groups?.some((g : any) => g.value !== group.value)
            }))
            return newGroupsOptions;
        }
        
        return newGroupsOptions;
    }, [role_id, organizations, isAdminRole, defaultOptions, isStudentRole, groups]);

    const renderField = (fieldName: string) => {
        if (fieldName === 'type') {
            return (
                <FormField
                    control={form.control}
                    name={fieldName}
                    render={({ field }) => (
                        <FormItem className="space-y-2">
                            <FormLabel>{t(`form.user.create.${field.name}`)}</FormLabel>
                            <FormControl>
                                <RadioGroup
                                    onValueChange={(value) => {
                                        form.register("password", { value: "" });
                                        form.register("confirm_password", { value: "" });
                                        if (value !== WITH_PASSWORD) {
                                            form.unregister(["password", "confirm_password"]);
                                        }
                                        field.onChange(value);  
                                    }}
                                    defaultValue={field.value}
                                    value={field.value}
                                    className="flex flex-col space-y-1"
                                >
                                    {defaultOptions['type'].map((option, index) => (
                                        <FormItem key={index} className="flex gap-2 items-center space-x-2 space-y-0">
                                            <FormControl>
                                                <RadioGroupItem value={option.value} checked={option.value === field.value} />
                                            </FormControl>
                                            <FormLabel className="font-normal">
                                                {t(`form.user.create.${option.label}`)}
                                            </FormLabel>
                                        </FormItem>
                                    ))}
                                </RadioGroup>
                            </FormControl>
                            <FormMessage />
                        </FormItem>
                    )}
                />
            );
        }

        if (fieldName === 'name') {
            return (
                <FormField
                    control={form.control}
                    name={"name"}
                    render={({ field }) => (
                        <FormItem className="space-y-2">
                            <FormLabel>{t(`form.user.create.${field.name}`)}</FormLabel>
                            <FormControl>
                                <Input
                                    {...field}
                                    placeholder={t(`form.user.create.${field.name}`)}
                                    type={"text"}
                                    disabled={field.disabled}
                                />
                            </FormControl>
                            <FormMessage />
                        </FormItem>
                    )}
                />
            );
        }


        if (fieldName === 'email_address') {
            return (
                <FormField
                    control={form.control}
                    name={fieldName}
                    render={({ field }) => (
                        <FormItem className="space-y-2">
                            <FormLabel>{t(`form.user.create.${field.name}`)}</FormLabel>
                            <FormControl>
                                <Input
                                    {...field}
                                    placeholder={t(`form.user.create.${field.name}`)}
                                    type={"text"}
                                    disabled={field.disabled}
                                />
                            </FormControl>
                            <FormMessage />
                        </FormItem>
                    )}
                />
            );
        }

        if (fieldName === 'password' || fieldName === 'confirm_password') {
            if (type !== WITH_PASSWORD) return null;
            
            return (
                <FormField
                    control={form.control}
                    name={fieldName as any}
                    render={({ field }) => (
                        <FormItem className="space-y-2">
                            <FormLabel>{t(`form.user.create.${field.name}`)}</FormLabel>
                            <FormControl>
                                <PasswordInput
                                    id={t(`form.user.create.${field.name}`)}
                                    value={field.value}
                                    onChange={field.onChange}
                                    autoComplete={t(`form.user.create.${field.name}`)}
                                    disabled={field.disabled}
                                    placeholder={t(`form.user.create.${field.name}`)}
                                    required={type === WITH_PASSWORD}
                                />
                            </FormControl>
                            <FormMessage />
                        </FormItem>
                    )}
                />
            );
        }

        if (fieldName === 'role_id') {
            return (
                <FormField
                    control={form.control}
                    name={fieldName}
                    render={({ field }) => (
                        <FormItem className="space-y-2">
                            <FormLabel>{t(`form.user.create.${field.name}`)}</FormLabel>
                            <Select
                                onValueChange={value => {
                                    const roleItem = defaultOptions.role_id.find(role => role.id === value);
                                    if (!roleItem) return;

                                    if ([].join(
                                        ...ROLE_ADMIN_ARRAY,
                                        ...ROLE_STATE_MANAGER_ARRAY,
                                        ...ROLE_REGIONAL_MANAGER_ARRAY,
                                        ...ROLE_COUNTY_MANAGER_ARRAY
                                    ).includes(roleItem.label)) {
                                        form.unregister(['organizations', 'groups']);
                                    } 

                                    if (ROLE_SCHOOL_MANAGER_ARRAY.includes(roleItem.label)) {
                                        form.register("organizations", { value: [] });
                                        form.setValue("organizations", []);
                                    }

                                    if (ROLE_PROFESSOR_ARRAY.includes(roleItem.label)) {
                                        form.register("organizations", { value: [] });
                                        form.register("groups", { value: [] });
                                        form.setValue("organizations", []);
                                        form.setValue("groups", []);
                                    }

                                    if (ROLE_STUDENT_ARRAY.includes(roleItem.label)) {
                                        form.register("organizations", { value: [] });
                                        form.register("groups", { value: [] });
                                        form.setValue("organizations", []);
                                        form.setValue("groups", []);
                                    }

                                    field.onChange(value);
                                }}
                                defaultValue={field.value}
                                value={field.value}
                                disabled={field.disabled}
                            >
                                <FormControl>
                                    <SelectTrigger>
                                        <SelectValue placeholder={t(`form.user.create.${field.name}`)} />
                                    </SelectTrigger>
                                </FormControl>
                                <SelectContent>
                                    {defaultOptions['role_id'].map((option, index) => (
                                        <SelectItem key={index} value={option.value}>
                                            {option.label}
                                        </SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                            <FormMessage />
                        </FormItem>
                    )}
                />
            );
        }

        if (fieldName === 'organizations') {
            if (isEmpty(role_id) || isAdminRole() || isStateManagerRole() || isRegionManagerRole() || isCountyManagerRole()) return null;

            return (
                <FormField
                    control={form.control}
                    name={fieldName}
                    render={({ field }) => (
                        <FormItem className="space-y-2">
                            <FormLabel>{t(`form.user.create.${field.name}`)}</FormLabel>
                            <MultipleSelector
                                disabled={field.disabled}
                                className="outline-none focus:outline-none focus:ring-0 focus-within:ring-0"
                                value={field.value as any}
                                onChange={(value) => {
                                    if (isEmpty(value)) {
                                        field.onChange(value)
                                        return;
                                    }

                                    // change groups when there is a group already selected
                                    if (groups) {
                                        const organizationIds = value.map((organization: any) => organization.id);
                                        const newGroupsValue : any = form.watch("groups")?.filter((group: any) =>
                                            organizationIds?.includes(group.organization.id)
                                        );
                                        form.setValue('groups', newGroupsValue);
                                    }
                                        
                                    field.onChange(value)
                                }}
                                placeholder={t(`form.user.create.${field.name}`)}
                                hidePlaceholderWhenSelected
                                emptyIndicator={
                                    <p className="text-center text-sm leading-10 text-gray-600 dark:text-gray-400 pl-2">
                                        {t('form.user.create.no_results')}
                                    </p>
                                }
                                onSearch={async (value) => {
                                    const organizations = getOrganizationsOptions();
                                    if (!value) return organizations;

                                    // filter by string search
                                    const filteredOptions = organizations.filter((organization: TOption) => 
                                        organization.label.toLowerCase().includes(value.toLowerCase())
                                    );

                                    return filteredOptions;
                                }}
                                triggerSearchOnFocus
                            />
                            <FormMessage />
                        </FormItem>
                    )}
                />
            );
        }

        if (fieldName === 'groups') {
            if (isEmpty(role_id) || isAdminRole() || isEmpty(organizations) || isStateManagerRole() || isRegionManagerRole() || isCountyManagerRole() || isSchoolManagerRole()) return null;

            return (
                <FormField
                    control={form.control}
                    name={fieldName}
                    render={({ field }) => (
                        <FormItem className="space-y-2">
                            <FormLabel>{t(`form.user.create.${field.name}`)}</FormLabel>
                            <MultipleSelector
                                disabled={field.disabled}
                                className="outline-none focus:outline-none focus:ring-0 focus-within:ring-0"
                                value={field.value as any}  
                                onChange={field.onChange}
                                placeholder={t(`form.user.create.${field.name}`)}
                                hidePlaceholderWhenSelected
                                emptyIndicator={
                                    <p className="text-center text-sm leading-10 text-gray-600 dark:text-gray-400 pl-2">
                                        {t('form.user.create.no_results')}
                                    </p>
                                }
                                onSearch={async (value) => {
                                    const options = getGroupsOptions();
                                    if (!value) return options;

                                    const filteredOptions = options.filter((group: TOption) => 
                                        group.label.toLowerCase().includes(value.toLowerCase())
                                    );

                                    return filteredOptions;
                                }}
                                triggerSearchOnFocus
                            />
                            <FormMessage />
                        </FormItem>
                    )}
                />
            );
        }

        if (fieldName === 'state') {
            if (isEmpty(role_id) || !isStateManagerRole()) return null;

            return (
                <FormField
                    control={form.control}
                    name={fieldName}
                    render={({ field }) => (
                        <FormItem className="space-y-2">
                            <FormLabel>{t(`form.user.create.${field.name}`)}</FormLabel>
                            <Select
                                onValueChange={field.onChange}
                                defaultValue={field.value}
                                value={field.value}
                                disabled={field.disabled}
                            >
                                <FormControl>
                                    <SelectTrigger>
                                        <SelectValue placeholder={t(`form.user.create.${field.name}`)} />
                                    </SelectTrigger>
                                </FormControl>
                                <SelectContent>
                                    {defaultOptions['organizations_utils']['state'].map((option, index) => (
                                        <SelectItem key={index} value={option}>
                                            {option}
                                        </SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                            <FormMessage />
                        </FormItem>
                    )}
                />
            );
        }

        if (fieldName === 'region') {
            if (isEmpty(role_id) || !isRegionManagerRole()) return null;

            return (
                <FormField
                    control={form.control}
                    name={fieldName}
                    render={({ field }) => (
                        <FormItem className="space-y-2">
                            <FormLabel>{t(`form.user.create.${field.name}`)}</FormLabel>
                            <Select
                                onValueChange={field.onChange}
                                defaultValue={field.value}
                                value={field.value}
                                disabled={field.disabled}
                            >
                                <FormControl>
                                    <SelectTrigger>
                                        <SelectValue placeholder={t(`form.user.create.${field.name}`)} />
                                    </SelectTrigger>
                                </FormControl>
                                <SelectContent>
                                    {defaultOptions['organizations_utils']['region'].map((option, index) => (
                                        <SelectItem key={index} value={option}>
                                            {option}
                                        </SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                            <FormMessage />
                        </FormItem>
                    )}
                />
            );
        }

        if (fieldName === 'county') {
            if (isEmpty(role_id) || !isCountyManagerRole()) return null;

            return (
                <FormField
                    control={form.control}
                    name={fieldName}
                    render={({ field }) => (
                        <FormItem className="space-y-2">
                            <FormLabel>{t(`form.user.create.${field.name}`)}</FormLabel>
                            <Select
                                onValueChange={field.onChange}
                                defaultValue={field.value}
                                value={field.value}
                                disabled={field.disabled}
                            >
                                <FormControl>
                                    <SelectTrigger>
                                        <SelectValue placeholder={t(`form.user.create.${field.name}`)} />
                                    </SelectTrigger>
                                </FormControl>
                                <SelectContent>
                                    {defaultOptions['organizations_utils']['county'].map((option, index) => (
                                        <SelectItem key={index} value={option}>
                                            {option}
                                        </SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                            <FormMessage />
                        </FormItem>
                    )}
                />
            );
        }

        return null;
    }

    if (isLoadingRoles || isLoadingOrganizations || isLoadingGroups || isLoadingOrganizationUtils) return <SkeletonSheet />;

    if (
        isEmpty(defaultOptions['role_id']) ||
        isEmpty(defaultOptions['type']) ||
        isEmpty(defaultOptions['organizations']) ||
        isEmpty(defaultOptions['groups']) || 
        isEmpty(defaultOptions['organizations_utils'])
    ) {
        return null;
    }

    return (
        <>
            <Form {...form}>
                <form onSubmit={form.handleSubmit(onSubmit)} className="w-full space-y-2">
                    <div className="grid space-y-2">
                        {Object.keys(formData.defaultValues).map((fieldName) => {
                            const field = renderField(fieldName);
                            if (!field) return null;
                            
                            return (
                                <fieldset key={fieldName} className="w-full field-item">
                                    {field}
                                </fieldset>
                            )
                        })}
                    </div>
                    <div className="pt-5 w-full">
                        <Button type="submit" variant={"secondary"} disabled={loading} className="!w-full">
                            { !loading ?  t('form.user.create.confirm') : <Loading style="horizontal" text={true} size={16}/>}
                        </Button>
                    </div>
                </form>
            </Form>
        </>
    )
}

export default FormCreateUser;