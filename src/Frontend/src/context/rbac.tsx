import { IRBACContext, IRBACProvider, IRBACWrapper } from "@/interfaces/rbac";
import { PropsWithChildren, createContext, useContext, useEffect, useState } from "react";
import { useAuth } from "./auth";

const RBACContext = createContext<IRBACContext>({} as IRBACContext);

const RBACProvider: React.FC<IRBACProvider> = ({ children, roles, scopes } : PropsWithChildren<IRBACProvider>) => {
    const [mounted, setMounted] = useState<boolean>(false);

    const { user } = useAuth();

    useEffect(() => {
        setMounted(true);
        return () => setMounted(false);
    }, []);

    const hasScopePermission  = (requiredScopes : Array<string>) => {
        return requiredScopes.some((element : string) => user?.scopes && user?.scopes.includes(element));
    }

    if (!mounted) return null;

    return (
        <RBACContext.Provider value={{ scopes, roles, hasScopePermission }}>
            {children}
        </RBACContext.Provider>
    );
}

const useRBAC = () => {
    const context = useContext(RBACContext);

    if (!context) { 
        throw new Error('useRBAC needs a RBACProvider')
    }

    return context;
}

const RBACWrapper : React.FC<IRBACWrapper> = ({ children, requiredRoles, requiredScopes }) => {
    const { user } = useAuth();

    if (!user || !user.scopes) return <div>403 - Unauthorized</div>;

    const hasRequiredScopes : boolean = requiredScopes.some((element : string) => user.scopes && user?.scopes.includes(element));

    if (hasRequiredScopes) {
        return children;
    }

    return null;
}



export { useRBAC, RBACProvider, RBACWrapper };