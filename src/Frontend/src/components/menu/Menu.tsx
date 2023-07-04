import { ICON_ACADEMIC_CAP, ICON_ARROW_LEFT_ON_RECTANGLE, ICON_BUILDING_LIBRARY, ICON_CHART_PIE, ICON_CHEVRON_DOWN, ICON_CHEVRON_RIGHT, ICON_COG, ICON_DOCUMENT_TEXT, ICON_HOME, ICON_PRESENTATION_CHART_BAR, ICON_USER, ICON_USER_GROUP, ICON_X_MARK } from "@/constants/icons";
import { SCOPE_ADMIN, SCOPE_DASHBOARD_VIEWER, SCOPE_LEARNER } from "@/constants/rbac";
import { useRBAC } from "@/context/rbac";
import useClickOutside from "@/hooks/useClickOutside/useClickOutside";
import useIcon from "@/hooks/useIcon/useIcon";
import { IMenuItem } from "@/interfaces/menu";
import { ISettingsStore } from "@/interfaces/store";
import { useSettingsStore } from "@/store/settings";
import Image from "next/image";
import { useRouter } from "next/router";
import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import Profile from "../profile/Profile";

const Menu : React.FC = () => {
    const router = useRouter();
    const { asPath } = router;

    const { t } = useTranslation();
    const { menu, setSettings } : ISettingsStore = useSettingsStore();
    const { getIcon } = useIcon();
    const { hasScopePermission } = useRBAC();

    const menuRef = useRef<HTMLElement>(null);
    const [mounted, setMounted] = useState<boolean>(false);
    const [menuItems, setMenusItems] = useState<Array<IMenuItem>>([
        // { name: 'home', icon: ICON_HOME, label: 'home', render: hasScopePermission([SCOPE_ADMIN]) },
        { name: 'reports', icon: ICON_PRESENTATION_CHART_BAR, label: 'reports', render: hasScopePermission([SCOPE_ADMIN, SCOPE_DASHBOARD_VIEWER]), route: '/reports',
            items: [
                { name: 'dashboard', icon: ICON_CHART_PIE, label: 'dashboard', render: hasScopePermission([SCOPE_DASHBOARD_VIEWER, SCOPE_ADMIN]), route: '/reports/dashboard' },
                { name: 'learners', icon: ICON_USER_GROUP, label: 'learners', render: hasScopePermission([SCOPE_DASHBOARD_VIEWER, SCOPE_ADMIN]), route: '/reports/learners'  },
            ],
            open: asPath.includes("reports"),
        },
        { name: 'exams', icon: ICON_DOCUMENT_TEXT, label: 'exams', render: hasScopePermission([SCOPE_LEARNER]), route: '/exams' },
        { name: 'admin', icon: ICON_COG, label: 'admin', render: hasScopePermission([SCOPE_ADMIN]), route: '/admin', 
            items: [
                { name: 'exams', icon: ICON_DOCUMENT_TEXT, label: 'exams', render: hasScopePermission([SCOPE_ADMIN]), route: '/admin/exams', order: 5 },
                { name: 'users', icon: ICON_USER_GROUP, label: 'users', render: hasScopePermission([SCOPE_ADMIN]), route: '/admin/users', order: 4  },
                { name: 'roles', icon: ICON_USER, label: 'roles', render: false, route: '/admin/roles', order: 3  },
                { name: 'groups', icon: ICON_ACADEMIC_CAP, label: 'groups', render: hasScopePermission([SCOPE_ADMIN]), route: '/admin/groups', order: 2 },
                { name: 'organizations', icon: ICON_BUILDING_LIBRARY, label: 'organizations', render: hasScopePermission([SCOPE_ADMIN]), route: '/admin/organizations', order: 1  },
            ],
            open: asPath.includes("admin")
        },
    ]);
    
    useEffect(() => {
        setMounted(true);
        return () => {
            setMounted(false);
        }
    }, [setMenusItems]);


    useClickOutside(menuRef, () => setSettings("menu", false));


    const handleMenuClick = (menu : IMenuItem) => {
        if (menu.items) {
            const newMenuItems = Object.assign([], menuItems);
            newMenuItems.map((m : IMenuItem) => {
                if (m.name === menu.name) {
                    m.open = !m.open
                } else {
                    m.open = false;
                }
            })
            setMenusItems(newMenuItems);
            return;
        }
        router.push(menu.route);
        setSettings("menu", false);
    }
    
    if (!mounted) return null;
    
    const renderMenuItem = (menuItem : IMenuItem) => {
        if (!menuItem.render) return null;
        
        return (
            <>
                <button 
                    className={`h-full flex gap-2 items-center min-h-[56px] text-white rounded-lg
                        hover:bg-white/5 w-full p-2
                        ${ menuItem.open || (asPath.includes(menuItem.name) && !menuItem.items) ? 'bg-white/10 hover:bg-white/10' : '' }`
                    }
                    onClick={() => handleMenuClick(menuItem)} 
                >
                    <div className="w-7 h-7 sm:w-8 sm:h-8 ml-2">
                        {getIcon({ icon: menuItem.icon, classes: "text-white" })}
                    </div>
                    <span className="ml-2">
                        {t(menuItem.label, { ns: "routes" })}
                    </span>
                    {menuItem.items ? 
                        <div className="flex-auto flex justify-end">
                            <div className="w-5 h-5">
                                {getIcon({ icon: menuItem.open ? ICON_CHEVRON_DOWN : ICON_CHEVRON_RIGHT, classes: "text-white" })}
                            </div>
                        </div>
                        : 
                        null
                    }
                </button>
                {menuItem.open ? 
                    <>
                        <div 
                            className={`flex transition ease-in-out delay-150 flex-col w-full rounded-lg p-2 bg-white/10 hover:bg-white/10 gap-1`} 
                        >
                            
                            {menuItem.items && menuItem.items.map((item : IMenuItem) => {
                                if (!item.render) return null;
                                
                                return (
                                    <div key={item.name} className={`h-14 w-full`} style={{ order: item.order }}>
                                        {renderMenuItem(item)}
                                    </div>
                                );
                            })}
                            
                        </div>
                    </>
                    :
                    null
                }
                
            </>
        )
    }

    return (
        <>
            {/* aside menu */}
            {menu && (
                <>
                    <div className="w-screen h-screen backdrop-blur-sm z-50 absolute transition-all">
                        <aside ref={menuRef} className={`w-full h-full absolute top-0 transition-all flex flex-col z-50 sm:w-5/12 bg-blue-600 sm:bg-blue-600 shadow-4xl sm:max-w-[400px]`}>
                            <div className='flex w-full bg-blue-700'>
                                <div className="flex justify-between w-full items-center h-full">
                                    <div className="px-4 py-5 cursor-pointer" onClick={() => setSettings("menu", false)}>
                                        <div className="w-6 h-6">
                                            {getIcon({ icon: ICON_X_MARK, classes: "text-white" })}
                                        </div>
                                    </div>
                                    <div className="relative h-[50px] w-[90px] sm:mr-5 mr-3">
                                        <Image
                                            src="/assets/images/logo.png" 
                                            alt="logo" 
                                            fill
                                            sizes="(max-width: 768px) 100vw"
                                            priority
                                        />
                                    </div>
                                </div>
                            </div>
                            <div className='h-full flex flex-col gap-1 items-center text-sm sm:text-xl pt-10 overflow-y-auto'>
                        
                                {menuItems.map((menu : IMenuItem, index : number) => {
                                    if (!menu.render) return null;

                                    return(
                                        <div 
                                            key={index} 
                                            className={`w-full gap-1 px-10 grid transition-all ${menu.items ? "" : "h-14"} items-center `}
                                        >
                                            {renderMenuItem(menu)}
                                        </div>
                                    );
                                })}
                            </div>
                            <div 
                                className="h-20 text-sm sm:text-xl flex items-center justify-center border-t bg-blue-700 border-blue-600 shadow-lg"    
                            >
                                <Profile />
                            </div>
                        </aside>
                    </div>
                </>
            )}
        </>
    )
}

export default Menu;

