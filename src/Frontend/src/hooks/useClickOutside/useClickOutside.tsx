import { useEffect, RefObject } from 'react';

const useClickOutside = <T extends HTMLElement>(ref: RefObject<T>, handler: () => void) => {
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (ref.current && !ref.current.contains(event.target as Node)) {
                handler();
            }
        };

        document.addEventListener('mousedown', handleClickOutside);

        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, [ref, handler]);
};

export default useClickOutside;