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
const SplashScreen : React.FC = () => {
    return (
        <>
            <div className="flex w-screen h-screen items-center justify-center bg-blue-500">
                <div className="flex p-2 text-white text-4xl animate-pulse">
                    STT
                </div>
            </div>
        </>
    )
}

export default SplashScreen;