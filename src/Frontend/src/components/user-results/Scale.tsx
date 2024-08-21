import React from 'react';
import { useTranslations } from 'next-intl';

import { ChevronDownIcon } from 'lucide-react';

interface ScaleProps {
  options: string[];
  selectedValue: string;
  classes: string;
}

const Scale: React.FC<ScaleProps> = ({ options, selectedValue, classes }) => {
    const t = useTranslations('results.classification');

    return (
        <div className="sm:relative flex items-center justify-center text-sm mb-2 w-full px-4">
            <div className={`sm:grid sm:grid-flow-col w-full ${classes}`}>
                {options.map((value, index) => {
                    return (
                        <div 
                            key={index}
                            className={`p-1 sm:h-2 w-full ${selectedValue.toLowerCase() === value ? 'text-base sm:text-sm' : 'hidden sm:grid'} sm:relative`}
                        >
                            {selectedValue.toLowerCase() === value && 
                            <>
                                <div className='sm:absolute hidden sm:flex justify-center bottom-2 left-0 right-0'>
                                    <div className='w-5 h-5'>
                                        <ChevronDownIcon className='text-destructive dark:text-white' />
                                    </div>
                                </div>
                            </>
                            }
                            <span className={`flex text-center justify-center sm:absolute sm:top-3 font-semibold md:text-xs lg:text-sm sm:left-0 sm:right-0 text-black dark:text-white`}>
                                {t(value)}
                            </span>
                        </div>
                    );
                })}
            </div>
        </div>
    );
};

export default Scale;
