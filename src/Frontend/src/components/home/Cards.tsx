import { SCOPE_ADMIN } from "@/constants/rbac";
import { useRBAC } from "@/context/rbac";
import { IPaginationStore } from "@/interfaces/store";
import { getAllGroups } from "@/services/group";
import { getAllOrganizations } from "@/services/organization";
import { getUsers } from "@/services/user";
import { usePaginationStore } from "@/store/pagination";
import { useQuery } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import Link from "next/link";
import React from "react";
import SkeletonCard from "../skeletons/SkeletonCard";

interface CardProps {
  label: string;
  total: number;
  route: string;
}

const Card: React.FC<CardProps> = ({ label, total, route }) => {
    const t = useTranslations("home.cards");

    if (!total) return <SkeletonCard />;

    return (
        <div className="w-full lg:max-w-72 cursor-pointer h-48 rounded-[12px] shadow-sm shadow-black/20 bg-black/5 dark:bg-white/10 overflow-hidden">
            <div className="w-full h-full relative p-6 flex flex-col justify-between items-start">
                <div>
                    <h4 className="text-[18px] font-semibold text-primary dark:text-white mb-2">
                        {t(`titles.${label}`)}
                    </h4>
                    <h3 className="text-sm text-black/80 dark:text-white/50">
                        {t("descriptions.group")}
                    </h3>
                </div>
                <div className="w-full flex justify-between">
                    <h3 className=" text-black/80 dark:text-white/50">{total}</h3>
                    <Link
                        href={route}
                        className="bg-primary dark:bg-darkPrimary hover:bg-primary-foreground dark:hover:bg-darkPrimary-foreground hover:transition-all px-5 py-2 rounded-[12px] text-white text-xs relative"
                    >
                        {t("buttons.view_group")}
                    </Link>
                </div>
            </div>
        </div>
    );
};

const CardOrganization: React.FC = () => {
    const t = useTranslations("home.cards");
    const { page }: IPaginationStore = usePaginationStore();
    const { hasScopePermission } = useRBAC();

    const { data, isLoading } = useQuery({
        queryKey: ["organizations", page],
        queryFn: () =>
            hasScopePermission([SCOPE_ADMIN]) ? getAllOrganizations() : null,
        retryOnMount: false,
        retry: false,
    });

    if (isLoading) return <SkeletonCard />;
    if (!data) return null;

    return (
        <div className="w-full lg:max-w-72 cursor-pointer h-48 rounded-[12px] shadow-sm shadow-black/20 bg-black/5 dark:bg-white/10 overflow-hidden">
            <div className="w-full h-full relative p-6 flex flex-col justify-between items-start">
                <div>
                    <h4 className="text-[18px] font-medium text-primary dark:text-white mb-2">
                        {t("titles.organizations")}
                    </h4>
                    <h3 className="text-sm text-black/80 dark:text-white/50">
                        {t("descriptions.organizations")}
                    </h3>
                </div>
                <div className="w-full flex items-center justify-between">
                    <h3 className=" text-black/80 dark:text-white/50">{data.total}</h3>
                    <Link
                        href={"/admin/organizations"}
                        className="bg-primary dark:bg-darkPrimary hover:bg-primary-foreground dark:hover:bg-darkPrimary-foreground hover:transition-all px-5 py-2 rounded-[12px] text-white text-xs relative"
                    >
                        {t("buttons.view_organizations")}
                    </Link>
                </div>
            </div>
        </div>
    );
};

const CardGroups: React.FC = () => {
    const t = useTranslations("home.cards");
    const { page }: IPaginationStore = usePaginationStore();
    const { hasScopePermission } = useRBAC();

    const { data, isLoading } = useQuery({
        queryKey: ["groups", page],
        queryFn: () => (hasScopePermission([SCOPE_ADMIN]) ? getAllGroups() : null),
        retryOnMount: false,
        retry: false,
    });

    if (isLoading) return <SkeletonCard />;
    if (!data) return null;

    return (
        <div className="w-full lg:max-w-72 cursor-pointer h-48 rounded-[12px] shadow-sm shadow-black/20 bg-black/5 dark:bg-white/10 overflow-hidden">
            <div className="w-full h-full relative p-6 flex flex-col justify-between items-start">
                <div>
                    <h4 className="text-[18px] font-medium text-primary dark:text-white mb-2">
                        {t("titles.groups")}
                    </h4>
                    <h3 className="text-sm text-black/80 dark:text-white/50">
                        {t("descriptions.groups")}
                    </h3>
                </div>
                <div className="w-full flex items-center justify-between">
                    <h3 className=" text-black/80 dark:text-white/50">{data.total}</h3>
                    <Link
                        href={"/admin/groups"}
                        className="bg-primary dark:bg-darkPrimary hover:bg-primary-foreground dark:hover:bg-darkPrimary-foreground hover:transition-all px-5 py-2 rounded-[12px] text-white text-xs relative"
                    >
                        {t("buttons.view_groups")}
                    </Link>
                </div>
            </div>
        </div>
    );
};

const CardUsers: React.FC = () => {
    const t = useTranslations("home.cards");
    const { page }: IPaginationStore = usePaginationStore();
    const { hasScopePermission } = useRBAC();

    const { data, isLoading } = useQuery({
        queryKey: ["users", page],
        queryFn: () => (hasScopePermission([SCOPE_ADMIN]) ? getUsers() : null),
        retryOnMount: false,
        retry: false,
    });

    if (isLoading) return <SkeletonCard />;
    if (!data) return null;

    return (
        <div className="w-full lg:max-w-72 cursor-pointer h-48 rounded-[12px] shadow-sm shadow-black/20 bg-black/5 dark:bg-white/10 overflow-hidden">
            <div className="w-full h-full relative p-6 flex flex-col justify-between items-start">
                <div>
                    <h4 className="text-[18px] font-medium text-primary dark:text-white mb-2">
                        {t("titles.users")}
                    </h4>
                    <h3 className="text-sm text-black/80 dark:text-white/50">
                        {t("descriptions.users")}
                    </h3>
                </div>
                <div className="w-full flex items-center justify-between">
                    <h3 className=" text-black/80 dark:text-white/50">{data.total}</h3>
                    <Link
                        href={"/admin/users"}
                        className='bg-primary dark:bg-darkPrimary hover:bg-primary-foreground dark:hover:bg-darkPrimary-foreground hover:transition-all px-5 py-2 rounded-[12px] text-white text-xs relative'
                    >
                        {t("buttons.view_users")}
                    </Link>
                </div>
            </div>
        </div>
    );
};

export { Card, CardOrganization, CardGroups, CardUsers };
