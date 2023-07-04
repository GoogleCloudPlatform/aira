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