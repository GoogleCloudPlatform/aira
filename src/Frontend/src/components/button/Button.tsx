import useIcon from "@/hooks/useIcon/useIcon";
import { IButton } from "@/interfaces/button";

const Button : React.FC<IButton> = ({ icon = undefined, action, name, disabled, classes, loading } : IButton) => {

    const { getIcon } = useIcon();
  
    return (
        <>
            <button 
                className={classes}
                onClick={action}
                disabled={disabled}
            >
                {icon ? 
                    <div className={`w-6 h-6 sm:w-8 sm:h-8`}>
                        {getIcon({ icon, classes: `text-white sm:text-gray-500 ${loading ? 'animate-pulse' : ""}` })}    
                    </div> 
                    : 
                    name
                }
            </button>
        </>
    )
}

export default Button;