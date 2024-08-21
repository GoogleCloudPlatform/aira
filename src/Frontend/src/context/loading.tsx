import { ILoadingContext } from "@/interfaces/loading";
import { PropsWithChildren, createContext, useContext, useState } from "react";

const LoadingContext = createContext<ILoadingContext>({} as ILoadingContext);

const LoadingProvider: React.FC<PropsWithChildren> = ({ children }) => {
    const [loading, setLoading] = useState<boolean>(false);

    return (
        <LoadingContext.Provider value={{ loading, setLoading }}>
            {children}
        </LoadingContext.Provider>
    );
};

const useLoading = () => {
    const context = useContext(LoadingContext);
    if (!context) {
        throw new Error('useLoading must be used within a LoadingProvider');
    }
    return context;
};

export { LoadingProvider, useLoading };
