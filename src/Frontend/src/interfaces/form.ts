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
export interface IInput {
    name: string;
    value: string | Array<string> | Array<any> | any;
    type: string;
    placeholder: string;
    label: string;
    required: boolean;
    options?: Array<IOption | any> | any;
    defaultOptions?: Array<IOption | any> | any; 
    multiple?: boolean;
    fields?: Array<IInput | any>;
    classes?: string; 
    disabled?: boolean;
    showLabel: boolean;
    render: boolean;
    dependencies?: Array<IDependence>;
    onChange?: (event : any) => void;
}

export interface IDependence {
    key: string;
    condition_values?: Array<string>;
    condition_multiple?: Array<string>;
    dynamic: boolean;
}

export interface IOption {
    name: string;
    id?: string;
    value?: string;
}