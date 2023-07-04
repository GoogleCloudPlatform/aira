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