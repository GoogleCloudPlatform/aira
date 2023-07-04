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
const ShimmerExam : React.FC = () => {
    return (
        <>
            <div className="relative w-full h-full flex flex-col gap-3 p-5">
                <div className="flex justify-center">
                    <div className="animate-pulse bg-gray-200 w-[300px] h-[100px] rounded-lg"></div>
                </div>
                <div className="animate-pulse h-[400px] bg-gray-200 w-full rounded-lg"></div>
                <div className="flex gap-20 items-center justify-center mt-10">
                    <div className="animate-pulse h-[150px] w-[150px] bg-gray-200 rounded-full"></div>
                    <div className="animate-pulse h-[200px] w-[200px] bg-gray-200 rounded-full"></div>
                    <div className="animate-pulse h-[150px] w-[150px] bg-gray-200 rounded-full"></div>
                </div>
            </div>
        </>
    )
}

export default ShimmerExam;