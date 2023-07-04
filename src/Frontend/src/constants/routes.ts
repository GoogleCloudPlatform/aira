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
export const ROUTES_ALLOWED_PATHS = [
    '/', '/es-ES', '/en-US', '/pt-BR',
    '/signin', '/es-ES/signin', '/en-US/signin', '/pt-BR/signin',
    '/signup', '/es-ES/signup', '/en-US/signup', '/pt-BR/signup'
];

export const ROUTES_SIGNED_PATHS = [
    '/admin', '/es-ES/admin', '/en-US/admin', '/pt-BR/admin',
    '/home', '/es-ES/home', '/en-US/home', '/pt-BR/home',
    '/exams', '/es-ES/exams', '/en-US/exams', '/pt-BR/exams',
    '/finish', '/es-ES/finish', '/en-US/finish', '/pt-BR/finish',
    '/admin', '/es-ES/admin', '/en-US/admin', '/pt-BR/admin',
    '/admin/organizations', '/es-ES/admin/organizations', '/en-US/admin/organizations', '/pt-BR/admin/organizations',
    '/admin/groups', '/es-ES/admin/groups', '/en-US/admin/groups', '/pt-BR/admin/groups',
    '/admin/roles', '/es-ES/admin/roles', '/en-US/admin/roles', '/pt-BR/admin/roles',
    '/admin/exams', '/es-ES/admin/exams', '/en-US/admin/exams', '/pt-BR/admin/exams',
    '/admin/users', '/es-ES/admin/users', '/en-US/admin/users', '/pt-BR/admin/users',
    '/reports', '/es-ES/reports', '/en-US/reports', '/pt-BR/reports',
    '/reports/dashboard', '/es-ES/reports/dashboard', '/en-US/reports/dashboard', '/pt-BR/reports/dashboard',
    '/reports/learners', '/es-ES/reports/learners', '/en-US/reports/learners', '/pt-BR/reports/learners'
];

export const ROUTES_SIGNED_PATHS_PARAMS = [
    '/exams/:id', '/es-ES/exams/:id', '/en-US/exams/:id', '/pt-BR/exams/:id'
]