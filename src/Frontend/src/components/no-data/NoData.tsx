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
import { useTranslation } from "react-i18next";

const NoData : React.FC<{ message?: string }> = ({ message = "no_data" }) => {
    const { t } = useTranslation();

    return (
        <>
            <div className='flex justify-center items-center p-1 md:p-10 w-full h-full overflow-x-hidden overflow-y-auto'>
                {t(message, { ns: "common" })}
            </div>
        </>
    );
}

export default NoData;