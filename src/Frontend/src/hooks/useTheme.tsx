import * as nextTheme from "next-themes";
import { useEffect, useState } from "react";
import { Switch } from "@/components/ui/switch"
import { LucideMoon, LucideSun } from "lucide-react";
import { Button } from "@/components/ui/button";

const useTheme = () => {
    const { theme, setTheme, resolvedTheme } = nextTheme.useTheme();

    const ThemeProvider = nextTheme.ThemeProvider;

    useEffect(() => {
        if (localStorage.theme === 'dark' || (!('theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
            setTheme('dark');
        } else {
            setTheme('light');
        }    
    }, [setTheme]);

    const toggleTheme = () => {   
        let newTheme = 'dark';
        
        if (theme === 'dark') newTheme = 'light';

        setTheme(newTheme);
    }

    const ButtonTheme : React.FC = () => {
        const active : boolean = theme === 'dark' ? true : false;

        return (
            <>
                <Button onClick={toggleTheme} size={"icon"} variant={"ghost"}>
                    {!active ? <LucideMoon className="w-5 h-5" /> : <LucideSun className="w-5 h-5" />}
                </Button>
            </>
        );
    }

    const ToggleTheme : React.FC = () => {
        const [mounted, setMounted] = useState<boolean>(false);

        useEffect(() => setMounted(true) ,[]);

        if (!mounted) return null;

        const active : boolean = theme === 'dark' ? true : false;

        return (
            <>
                <Switch 
                    checked={active} 
                    onCheckedChange={toggleTheme}
                    className="border-gray-200 data-[state=checked]:bg-white data-[state=unchecked]:bg-white"
                />
            </>
        );
    }

    return { ThemeProvider, toggleTheme, ToggleTheme, ButtonTheme, theme };
}

export default useTheme;