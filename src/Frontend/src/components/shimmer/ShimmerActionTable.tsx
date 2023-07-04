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
const ShimmerActionTable : React.FC = () => {
    return (
        <>
            <div className="relative w-full flex flex-col gap-3">
                <div className="flex justify-end">
                    <button className="w-[100px] animate-pulse h-10 bg-gray-200 rounded-lg"></button>
                </div> 
                <div className="table h-[365px] w-full animate-pulse bg-gray-200 rounded-lg" />
                <div className="pagination flex items-center justify-between px-4 py-3 sm:px-6 bg-gray-200 animate-pulse rounded h-10" />
            </div>
        </>
    )
}

export default ShimmerActionTable;