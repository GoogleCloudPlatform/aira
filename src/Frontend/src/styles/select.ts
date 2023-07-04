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
export const selectStyle = {
    control: (baseStyles : any, state : any) => ({
        ...baseStyles,
        borderColor: 'bg-gray-200',
        color: '#9ca3af',
        backgroundColor: state.isDisabled ? '#fafafa' : '',
        '&:hover': {
            cursor: "pointer"
        },
    }),
    menu: (baseStyles : any, state : any) => ({
        ...baseStyles,
        cursor: "pointer",
        zIndex: 100,
        //position: "relative"
    }),
    menuList: (baseStyles : any, state : any) => ({
        ...baseStyles,
        maxHeight: '120px',
        zIndex: 100,
        position: "relative",
        cursor: "pointer",
        color: '#6b7280',
    }),
    option: (baseStyles : any, state : any) => ({
        ...baseStyles,
        cursor: "pointer"
    }),
    singleValue: (baseStyles : any, state : any) => ({
        ...baseStyles,
        color: "#6b7280"
    }),
    valueContainer: (baseStyles : any, state : any) => ({
        ...baseStyles,
        maxHeight: "40px",
        overflowY: "auto",
        /* Hide scrollbar for Chrome, Safari and Opera */
        '&::-webkit-scrollbar': {
            display: 'none',
        },
        /* Hide scrollbar for IE, Edge and Firefox */
        'msOverflowStyle': 'none', /* IE and Edge */
        'scrollbarWidth': 'none', /* Firefox */
    }),
}