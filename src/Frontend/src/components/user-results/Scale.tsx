import React from 'react';
import { useTranslations } from 'next-intl';
import { ArrowDownIcon } from 'lucide-react';

interface ScaleProps {
  options: string[];
  selectedValue: string;
  classes: string;
}

const Scale: React.FC<ScaleProps> = ({ options, selectedValue, classes }) => {
    const t = useTranslations('results.classification');
    const normalizedSelected = selectedValue.toLowerCase();

    return (
        <div className="relative flex flex-col items-center justify-center text-sm w-full mt-6 mb-10 px-1 sm:px-4">
            {/* Segment Bar container */}
            <div className={`relative sm:grid sm:grid-flow-col w-full h-5 rounded-full overflow-visible ${classes} shadow-inner shadow-slate-900/5 border border-slate-100/20`}>
                {options.map((value, index) => {
                    const isSelected = normalizedSelected === value.toLowerCase();
                    return (
                        <div 
                            key={index}
                            className={`h-full w-full flex items-center justify-center relative ${isSelected ? 'flex' : 'hidden sm:flex'}`}
                        >
                            {isSelected && (
                                <div className='absolute -top-12 left-0 right-0 flex flex-col items-center animate-fade-in-up'>
                                    {/* Tooltip Pointer */}
                                    <div className='bg-indigo-600 text-white text-xs font-bold px-3 py-1.5 rounded-lg shadow-md shadow-indigo-200 dark:shadow-none flex items-center gap-1 whitespace-nowrap z-20'>
                                        <span className="relative flex h-2 w-2">
                                            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
                                            <span className="relative inline-flex rounded-full h-2 w-2 bg-white"></span>
                                        </span>
                                        {t(value)}
                                    </div>
                                    {/* Down Arrow */}
                                    <div className='w-4 h-4 -mt-1.5 text-indigo-600 flex justify-center z-10'>
                                        <ArrowDownIcon className='fill-indigo-600 stroke-[3px]' />
                                    </div>
                                </div>
                            )}
                            <span className={`absolute top-7 text-center font-bold md:text-[10px] lg:text-xs tracking-wide uppercase text-slate-600 dark:text-slate-400 ${isSelected ? 'text-indigo-600 dark:text-indigo-400 scale-105 font-extrabold' : 'opacity-70 sm:opacity-100'}`}>
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
