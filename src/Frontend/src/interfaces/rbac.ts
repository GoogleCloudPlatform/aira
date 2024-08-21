export interface IRBACContext {
    scopes: Array<string>;
    roles: Array<string>;
    hasScopePermission: (requiredScopes : Array<string>) => boolean;
}

export interface IRBACProvider {
    children: React.ReactNode;
    scopes: Array<string>;
    roles: Array<string>;
}

export interface IRBACWrapper {
    children: any;
    requiredRoles?: Array<string>;
    requiredScopes: Array<string>;
}