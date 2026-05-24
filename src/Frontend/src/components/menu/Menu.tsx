'use client'

import { ICON_ACADEMIC_CAP, ICON_BOOK_OPEN, ICON_BUILDING_LIBRARY, ICON_CHART_PIE, ICON_CHEVRON_DOWN, ICON_CHEVRON_UP, ICON_CLIPBOARD_CHECK, ICON_COG, ICON_DOCUMENT_TEXT, ICON_HOME, ICON_NOTEPAD_TEXT, ICON_PRESENTATION_CHART_BAR, ICON_TABLE_CELLS, ICON_USER, ICON_USER_GROUP, ICON_GLOBE, ICON_MAP, ICON_BUILDING, ICON_LIST_ORDERED, ICON_CLOCK, ICON_CLOUD_ARROW_UP } from '@/constants/icons';
import { SCOPE_ADMIN, SCOPE_DASHBOARD_VIEWER, SCOPE_EXAM_LIST, SCOPE_GROUP_LIST, SCOPE_ORGANIZATION_LIST, SCOPE_USER, SCOPE_USER_IMPERSONATE, SCOPE_USER_LIST } from '@/constants/rbac';
import { useRBAC } from '@/context/rbac';
import useIcon from '@/hooks/useIcon';
import { IMenuItem } from '@/interfaces/menu';
import { IPaginationStore, ISettingsStore } from '@/interfaces/store';
import { useSettingsStore } from '@/store/settings';
import { useTranslations } from 'next-intl';
import { useParams, usePathname, useRouter } from 'next/navigation';
import { PropsWithChildren, useEffect, useState } from 'react';
import Profile from '../profile/Profile';
import { cn } from '@/libs/shadcn/utils';
import { Link } from '@/router/link/Link';
import { usePaginationStore } from '@/store/pagination';
import { api } from '@/api/api';
import UploadTutorialModal from '../tutorials/UploadTutorialModal';

const Menu: React.FC = () => {
    const t = useTranslations("sidebar");
    const pathname = usePathname();
    const { locale } = useParams();
    const router = useRouter();

    const { menu, setSettings }: ISettingsStore = useSettingsStore();
    const { hasScopePermission } = useRBAC();
    const { getIcon } = useIcon();
    const { show_finished }: IPaginationStore = usePaginationStore();

    const [isUploadModalOpen, setIsUploadModalOpen] = useState<boolean>(false);
    const [mounted, setMounted] = useState<boolean>(false);
    const [menuItems, setMenusItems] = useState<Array<IMenuItem>>([
        {
            name: 'home',
            icon: ICON_HOME,
            label: 'home',
            render: hasScopePermission([SCOPE_DASHBOARD_VIEWER, SCOPE_ADMIN, SCOPE_USER]),
            route: '/home'
        },
        {
            name: 'reports',
            icon: ICON_PRESENTATION_CHART_BAR,
            label: 'reports',
            render: hasScopePermission([SCOPE_DASHBOARD_VIEWER, SCOPE_ADMIN, SCOPE_EXAM_LIST]),
            route: '/reports/dashboard',
        },
        {
            name: 'exams',
            icon: ICON_DOCUMENT_TEXT,
            label: 'exams',
            render: hasScopePermission([SCOPE_USER]),
            route: '/exams',
        },
        {
            name: 'admin',
            icon: ICON_COG,
            label: 'admin',
            render: hasScopePermission([SCOPE_ADMIN]),
            route: '/admin',
            items: [
                {
                    name: 'countries',
                    icon: ICON_GLOBE,
                    label: 'countries',
                    render: hasScopePermission([SCOPE_ADMIN]),
                    route: '/admin/locations/countries',
                    order: 1,
                },
                {
                    name: 'states',
                    icon: ICON_MAP,
                    label: 'states',
                    render: hasScopePermission([SCOPE_ADMIN]),
                    route: '/admin/locations/states',
                    order: 2,
                },
                {
                    name: 'cities',
                    icon: ICON_BUILDING,
                    label: 'cities',
                    render: hasScopePermission([SCOPE_ADMIN]),
                    route: '/admin/locations/cities',
                    order: 3,
                },
                {
                    name: 'series',
                    icon: ICON_LIST_ORDERED,
                    label: 'series',
                    render: hasScopePermission([SCOPE_ADMIN]),
                    route: '/admin/series',
                    order: 4,
                },
                {
                    name: 'shifts',
                    icon: ICON_CLOCK,
                    label: 'shifts',
                    render: hasScopePermission([SCOPE_ADMIN]),
                    route: '/admin/shifts',
                    order: 5,
                },
                {
                    name: 'organizations',
                    icon: ICON_BUILDING_LIBRARY,
                    label: 'organizations',
                    render: hasScopePermission([SCOPE_ORGANIZATION_LIST, SCOPE_ADMIN]),
                    route: '/admin/organizations',
                    order: 6,
                },
                {
                    name: 'groups',
                    icon: ICON_ACADEMIC_CAP,
                    label: 'groups',
                    render: hasScopePermission([SCOPE_GROUP_LIST, SCOPE_ADMIN]),
                    route: '/admin/groups',
                    order: 7,
                },
                {
                    name: 'roles',
                    icon: ICON_USER,
                    label: 'roles',
                    render: false,
                    route: '/admin/roles',
                    order: 8,
                },
                {
                    name: 'users',
                    icon: ICON_USER_GROUP,
                    label: 'users',
                    render: hasScopePermission([SCOPE_USER_LIST, SCOPE_ADMIN]),
                    route: '/admin/users',
                    order: 9,
                },
                {
                    name: 'exams',
                    icon: ICON_DOCUMENT_TEXT,
                    label: 'exams',
                    render: hasScopePermission([SCOPE_EXAM_LIST, SCOPE_ADMIN]),
                    route: '/admin/exams',
                    order: 10,
                },
            ],
            open: pathname.includes('admin'),
        },
        {
            name: 'groups',
            icon: ICON_ACADEMIC_CAP,
            label: 'groups',
            render: hasScopePermission([SCOPE_USER_IMPERSONATE]),
            route: '/groups',
        },
        {
            name: 'apply_exams',
            icon: ICON_NOTEPAD_TEXT,
            label: 'apply_exams',
            render: hasScopePermission([SCOPE_USER_IMPERSONATE]),
            route: '/users/exams',
            highlight: [
                '^\/users\/[0-9a-f]{8}\-[0-9a-f]{4}\-[0-9a-f]{4}\-[0-9a-f]{4}\-[0-9a-f]{12}\/exams.*$', // this regex captures everything that starts with /users/<uuid>/exams/<anything>
                '^\/users\/(?!.*results).*$'
            ],
        },
        {
            name: 'results',
            icon: ICON_CLIPBOARD_CHECK,
            label: 'results',
            render: hasScopePermission([SCOPE_USER_IMPERSONATE, SCOPE_USER]),
            route: '/users/results',
            highlight: [
                '^\/users\/[0-9a-f]{8}\-[0-9a-f]{4}\-[0-9a-f]{4}\-[0-9a-f]{4}\-[0-9a-f]{12}\/results$', // this regex captures everything that starts with /users/<uuid>/results
                //'^\/users\/[0-9a-f]{8}\-[0-9a-f]{4}\-[0-9a-f]{4}\-[0-9a-f]{4}\-[0-9a-f]{12}\/results.*$', // this regex captures everything that starts with /users/<uuid>/results/<anything>
                //'/users/results',
            ],
        },
        {
            name: 'tutorials',
            icon: ICON_BOOK_OPEN,
            label: 'tutorials',
            render: hasScopePermission([SCOPE_USER_IMPERSONATE, SCOPE_ADMIN]),
            route: '/tutorials',
            items: [
                {
                    name: 'user',
                    icon: ICON_DOCUMENT_TEXT,
                    label: 'learners',
                    render: false,
                    route: '/tutorials/user',
                    order: 1,
                },
                {
                    name: 'educator',
                    icon: ICON_ACADEMIC_CAP,
                    label: 'educators',
                    render: hasScopePermission([SCOPE_USER_IMPERSONATE, SCOPE_ADMIN]),
                    route: `https://storage.googleapis.com/${process.env.NEXT_PUBLIC_TUTORIAL_BUCKET}/tutorial/tutorialprofessor_${locale}.pdf`,
                    order: 2,
                    shouldRedirect: true,
                },
                {
                    name: 'admin',
                    icon: ICON_COG,
                    label: 'admin',
                    render: hasScopePermission([SCOPE_ADMIN]),
                    route: `https://storage.googleapis.com/${process.env.NEXT_PUBLIC_TUTORIAL_BUCKET}/tutorial/tutorialadministrador_${locale}.pdf`,
                    order: 3,
                    shouldRedirect: true,
                },
                {
                    name: 'upload',
                    icon: ICON_CLOUD_ARROW_UP,
                    label: 'upload_tutorial',
                    render: hasScopePermission([SCOPE_ADMIN]),
                    route: '#upload-tutorial-modal',
                    order: 4,
                },
            ],
        },
    ]);

    const fetchTutorialUrls = async () => {
        try {
            const [educatorRes, adminRes] = await Promise.all([
                api.get(`/tutorials/latest/educator?locale=${locale}`),
                api.get(`/tutorials/latest/admin?locale=${locale}`),
            ]);
            
            setMenusItems(prevItems => {
                return prevItems.map(item => {
                    if (item.name === 'tutorials') {
                        return {
                            ...item,
                            items: item.items?.map(subItem => {
                                if (subItem.name === 'educator' && educatorRes.data?.url) {
                                    return { ...subItem, route: educatorRes.data.url };
                                }
                                if (subItem.name === 'admin' && adminRes.data?.url) {
                                    return { ...subItem, route: adminRes.data.url };
                                }
                                return subItem;
                            })
                        };
                    }
                    return item;
                });
            });
        } catch (error) {
            console.error("Failed to fetch dynamic tutorial links", error);
        }
    };

    useEffect(() => {
        setMounted(true);
        fetchTutorialUrls();
        return () => {
            setMounted(false);
        };
    }, []);

    const handleMenuClick = (menu: IMenuItem) => {
        // control menu state (open/closed)]
        if (menu.items) {
            const newMenu = [...menuItems]

            const newMenuItems = newMenu?.map((item: IMenuItem) => {
                if (item.name === menu.name) {
                    return { ...item, open: !item.open }
                } else {
                    return { ...item, open: false }
                }
            });

            setMenusItems(newMenuItems);
            return;
        } else {
            const newMenu = [...menuItems]

            const newMenuItems = newMenu?.map((item: IMenuItem) => {
                const selectedMenu = item.items?.find(submenu => submenu.route === menu.route)

                if (selectedMenu) {
                    return { ...item, open: true }
                } else {
                    return { ...item, open: false }
                }
            })

            setMenusItems(newMenuItems);
        }

        if (menu.name === 'upload') {
            setIsUploadModalOpen(true);
            return;
        }

        if (menu.shouldRedirect) window.open(menu.route, '_blank');
        else {
            router.push(menu.route);
        }

        if (window.innerWidth < 768) {
            setSettings('menu', false);
        }
    };

    if (!mounted) return null;

    const renderMenuItem = (menuItem: IMenuItem) => {
        if (!menuItem.render) return null;

        const shouldHighlight = () => {
            const [_, testPathname] = pathname.split(`/${locale}`);

            let highlight = true; // Start with true, assuming all regex patterns will match
            if (menuItem.highlight && Array.isArray(menuItem.highlight)) {
                for (const regex of menuItem.highlight) {
                    if (!testPathname.match(new RegExp(regex))) { // If any regex does not match, set highlight to false
                        highlight = false;
                        break; // No need to continue checking once a mismatch is found
                    }
                }
            } else {
                highlight = false; // If highlight array is not defined or not an array, set highlight to false
            }
            return highlight;
        };

        const Tag: React.FC<any> = ({ children, ...props }: PropsWithChildren) => {
            if (menuItem.items || menuItem.route.startsWith('#')) {
                return (
                    <button {...props} onClick={() => handleMenuClick(menuItem)}>
                        {children}
                    </button>
                )
            }

            return (
                <Link {...props} href={menuItem.route} target='_blank'>
                    {children}
                </Link>
            );
        }


        return (
            <div
                className={cn(
                    'w-full rounded-lg hover:bg-white/5',
                    ((pathname.includes(menuItem.route) || shouldHighlight()) && !menuItem.items) && 'bg-white/5',
                    menuItem.open && 'bg-white/5 p-2'
                )}
            >
                <Tag
                    className={cn(
                        'flex items-center text-nowrap gap-4 w-full h-full p-2',
                        menu ? 'justify-start' : 'justify-center'
                    )}
                    title={!menu ? t(`options.${menuItem.label}`) : ''}
                >
                    <div className={`w-6 h-6`}>
                        <div className={`w-6 h-6`}>
                            {getIcon({ icon: menuItem.icon, classes: 'text-white' })}
                        </div>
                    </div>

                    <span
                        //className={`ml-2 text-white ${!menu ? 'md:hidden' : ''} `}
                        className={cn(
                            'ml-2 text-white flex-1 text-start',
                            !menu && 'md:hidden'
                        )}
                    >
                        {t(`options.${menuItem.label}`)}
                    </span>

                    {menuItem.items && (
                        <div
                            //className={`flex justify-end ${!menu ? 'md:hidden' : ''}`}
                            className={cn(
                                'flex justify-end ',
                                !menu && 'md:hidden'
                            )}
                        >
                            <div className='w-4 h-4'>
                                {getIcon({
                                    icon: menuItem.open ? ICON_CHEVRON_UP : ICON_CHEVRON_DOWN,
                                    classes: 'text-white',
                                })}
                            </div>
                        </div>
                    )}
                </Tag>

                {menuItem.open && (
                    <>
                        <ul className='mt-2 w-full flex flex-col gap-2'>
                            {menuItem.items && menuItem.items.map((item: IMenuItem) => {
                                if (!item.render) return null;
                                return (
                                    <li
                                        className='w-full'
                                        key={item.name}
                                        style={{ order: item.order }}
                                    >
                                        {renderMenuItem(item)}
                                    </li>
                                );
                            })}
                        </ul>
                    </>
                )}
            </div>
        );
    };

    return (
        <nav className='flex flex-col items-start w-full min-h-full'>
            <ul className='w-full flex flex-col h-full space-y-2'>
                {menuItems.map((menu: IMenuItem, index: number) => {
                    if (!menu.render) return null;

                    return (
                        <li key={index} className="relative">
                            {renderMenuItem(menu)}
                        </li>
                    );
                })}
            </ul>

            <div className='w-full'>
                <Profile />
            </div>
            <UploadTutorialModal 
                isOpen={isUploadModalOpen} 
                onClose={() => setIsUploadModalOpen(false)} 
                locale={locale as string} 
                onSuccess={fetchTutorialUrls} 
            />
        </nav>
    );
};

export default Menu;